from io import BytesIO
from typing import Union, List
from urllib.parse import urlparse
from PIL import Image, ImageDraw as ID, ImageFont, ImageOps
from aiohttp import ClientSession
from discord import File
from discord.ext.commands import command, Bot
import numpy as np
from webp import WebPAnimEncoder, WebPPicture, WebPAnimEncoderOptions

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class AsciiCog:
    def __init__(self, img_width: int = 512):
        self.width = img_width

        self.chars = np.asarray(list(' .,:;irsXA253hMHGS#9B&@'))
        self.image_scale = 0.5
        self.intensity = 1.2
        self.width_correction = 7 / 4
        self.default = ID.Draw(Image.new("RGB", (128, 128)))
        self.font = ImageFont.truetype("assets/CourierNew.ttf", 18)

    def get_height(self, img: Image.Image) -> int:
        w, h = img.size
        ratio = self.width / w
        new_height = h * ratio
        return new_height

    @staticmethod
    def get_invert(img: Image.Image) -> bool:
        data_img = np.sum(np.asarray(img))
        invert = np.sum(data_img >= data_img.max() - 5) < np.sum(data_img <= data_img.min() + 5)
        return bool(invert)

    def stringify(self, img: Image.Image, filename: str) -> BytesIO:
        file = urlparse(filename).path
        inv = self.get_invert(img)
        if file.endswith("gif"):
            self.width /= 2
            duration = img.info['duration']
            frames = self.stringify_gif(img, inv)
            gif = self.string_to_gif(frames, duration, inv)
            self.width *= 2
            return gif

        elif any(file.endswith(x) for x in ("png", "jpg", "jpeg")):
            string = self.stringify_image(img, inv)
            return self.string_to_png(string, inv)
        raise Exception("Unsupported file type")

    def stringify_gif(self, img: Image.Image, inv: bool = False) -> List[str]:
        frames = []
        current = img.convert("RGBA")
        while True:
            try:
                frames.append(self.stringify_image(current.convert("RGB"), inv))
                img.seek(img.tell()+1)
                current = Image.alpha_composite(current, img.convert('RGBA'))
            except EOFError:
                break

        return frames

    def string_to_gif(self, frames: List[str], duration: float, inv: bool = False) -> BytesIO:
        as_images = [self.string_to_png(frame, inv, True) for frame in frames]

        b = BytesIO()
        # as_images[0].save(b, format='gif', duration=duration/2, save_all=True, append_images=as_images[1:], loop=100)

        enc = WebPAnimEncoder.new(*as_images[0].size, WebPAnimEncoderOptions.new(minimize_size=True))
        t = 0
        for img in as_images:
            pic = WebPPicture.from_pil(img)
            enc.encode_frame(pic, round(t))
            t += duration

        data = enc.assemble(round(t))
        b.write(data.buffer())

        b.seek(0)
        return b

    def stringify_image(self, img: Image.Image, inv: bool = False) -> str:
        if inv:
            img = ImageOps.invert(img.convert("RGB"))
        new_size = (round(self.width * self.width_correction * self.image_scale),
                    round(self.get_height(img) * self.image_scale))

        data_img = np.sum(np.asarray(img.resize(new_size)), axis=2)
        data_img -= data_img.min()

        scaled_img = (1.0 - data_img / data_img.max()) ** self.intensity * (self.chars.size - 1)

        stringified_img = "\n".join(
            "".join(r)
            for r in self.chars[scaled_img.astype(int)]
        )

        return stringified_img

    def string_to_png(self, ascii_: str, inv: bool = False, as_img: bool = False) -> Union[BytesIO, Image.Image]:
        w, h = self.default.textsize(ascii_, font=self.font)
        blank = Image.new("RGB", (w, h), [WHITE, BLACK][inv])
        draw = ID.Draw(blank)
        draw.text((0, 0), ascii_, [BLACK, WHITE][inv], font=self.font)
        if as_img:
            return blank
        fp = BytesIO()
        blank.save(fp, format="png")
        fp.seek(0)
        return fp

    @command()
    async def ascii(self, ctx, image_url: str):
        async with ClientSession as session:
            async with session.get(image_url) as response:
                data: bytes = await response.read()

        img = Image.open(BytesIO(data))
        inv = self.get_invert(img)
        stringified = self.stringify_image(img, inv)
        reimaged = self.string_to_png(stringified, inv)
        await ctx.send(file=File(reimaged, filename="ascii.png"))


def setup(core: Bot):
    core.add_cog(AsciiCog(core))
