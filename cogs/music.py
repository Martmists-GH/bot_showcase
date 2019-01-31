from collections import defaultdict
from typing import Dict, Type

from discord import FFmpegPCMAudio, PCMAudio, AudioSource
from discord.ext.commands import group, Context, Bot
from mart_music.async_ import MusicClient
from mart_music.common import Song

from core.music.player import Player
from core.music.queues import QUEUE, Queue
from core.music.sources import MartPCMAudio, MartFFmpegPCMAudio


class MusicCog:
    def __init__(self, core, queue_type: Type[Queue] = QUEUE.Chunked):
        self.core = core
        self._type = queue_type
        self.client = MusicClient(core.config["music_token"])
        self.players: Dict[str, Player] = {}

    async def _play(self, ctx: Context, source: AudioSource):
        if ctx.guild.id not in self.players:
            self.players[ctx.guild.id] = Player(
                await ctx.author.voice.channel.connect(reconnect=True),
                self._type()
            )

        self.players[ctx.guild.id].play(source)

    @staticmethod
    def no_choice(ctx):
        return ctx.send("Not a valid choice or no choice given!")

    @group()
    def music(self):
        pass

    @music.command()
    def play(self, ctx: Context, *, song: str):
        results = await self.client.search(song)

        msg = "\n".join(f"{i+1}: {song.title} - {song.artist}" for i, song in enumerate(results))

        await ctx.send(f"```\n{msg}```")

        msg = await ctx.guild.wait_for('message',
                                       check=lambda m: m.author == ctx.author,
                                       timeout=60)

        if not msg:
            return await self.no_choice(ctx)

        if not msg.content.isdigit():
            return await self.no_choice(ctx)

        choice = int(msg.content)
        result = [song for i, song in enumerate(results) if i + 1 == choice]
        if not result:
            return await self.no_choice(ctx)

        choice: Song = result[0]

        if choice.downloadable:
            source = MartPCMAudio((await self.client.download(choice))[0], choice)
        else:
            source = MartFFmpegPCMAudio((await self.client.download(choice))[0], choice)

        self.play(ctx, source)


def setup(core: Bot):
    core.add_cog(MusicCog(core))
