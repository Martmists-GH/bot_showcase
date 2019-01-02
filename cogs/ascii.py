from io import BytesIO

from PIL import Image, ImageDraw as ID, ImageFont, ImageOps
from aiohttp import ClientSession
from discord import File
from discord.ext.commands import command

import numpy as np


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

    def get_height(self, img: Image) -> int:
        w, h = img.size
        ratio = self.width / w
        new_height = h * ratio
        return new_height

    @staticmethod
    def get_invert(img: Image) -> bool:
        data_img = np.sum(np.asarray(img), axis=2)
        invert = np.sum(data_img >= data_img.max() - 5) < np.sum(data_img <= data_img.min() + 5)
        return bool(invert)

    def stringify(self, img: Image, inv: bool = False) -> str:
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

    def string_to_png(self, ascii_: str, inv: bool = False) -> BytesIO:
        w, h = self.default.textsize(ascii_, font=self.font)
        blank = Image.new("RGB", (w, h), [WHITE, BLACK][inv])
        draw = ID.Draw(blank)
        draw.text((0, 0), ascii_, [BLACK, WHITE][inv], font=self.font)
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
        stringified = self.stringify(img, inv)
        reimaged = self.string_to_png(stringified, inv)
        await ctx.send(file=File(reimaged, filename="ascii.png"))


def setup(core):
    pass


def test(core):
    cog = AsciiCog()

    def test_file(f: str):
        img = Image.open(f)
        inv = cog.get_invert(img)
        text = cog.stringify(img, inv)
        print(text)
        bytes_io = cog.string_to_png(text, inv)
        img = Image.open(bytes_io)
        img.show()
        img.save(f"{f}_test.png")

    test_file("assets/avatar_discord.png")
    test_file("assets/avatar_discord_2.png")
    test_file("assets/avatar_discord_3.png")
    test_file("assets/lewd.png")
