import audioop
from io import BytesIO
from typing import Type

from discord import PCMAudio, FFmpegPCMAudio, AudioSource
from izunadsp import DSPServer
from mart_music.common import Song


class MartAudio(AudioSource):
    def __init__(self, origin: Song):
        self.origin = origin

    def to(self, cls: Type[AudioSource], **kwargs):
        return cls(self.source, **kwargs)


class MartPCMAudio(PCMAudio, MartAudio):
    def __init__(self, source: BytesIO, origin: Song):
        MartAudio.__init__(self, origin)
        PCMAudio.__init__(self, source)


class MartFFmpegPCMAudio(FFmpegPCMAudio, MartAudio):
    def __init__(self, source: BytesIO, origin: Song):
        MartAudio.__init__(self, origin)
        FFmpegPCMAudio.__init__(self, source)


class CrossfadeSource(AudioSource):
    def __init__(self, source: AudioSource, steps: int = 10, fade: bool = True):
        self.current_source = source
        self.overlay_source = None

        self.fade = fade
        self.step = 1/(2 * steps)
        self._pos = 0

    def read(self):
        if self.overlay_source is None:
            return self.current_source.read()

        current = self.current_source.read()
        overlay = self.overlay_source.read()

        if not current:
            self.current_source = self.overlay_source
            self.overlay_source = None
            return overlay

        if not overlay:
            self.overlay_source = None
            return current

        if self.fade:
            vol = self.step * self._pos
            sub = 1 - vol
            self._pos += 1

            current = audioop.mul(current, 2, sub)
            overlay = audioop.mul(overlay, 2, vol)

        return audioop.add(current, overlay, 2)

    def is_opus(self):
        return False


class DSPSource(AudioSource):
    def __init__(self, source: AudioSource, server: DSPServer):
        self.source = source
        self.server = server

    def read(self):
        file = BytesIO(self.source.read())
        manager = self.server.get_manager()
        res_file = manager.passthrough(file, suffix=".opus")
        return res_file.read()

    def is_opus(self):
        return True
