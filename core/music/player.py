from io import BytesIO
from typing import Dict

from discord import VoiceClient, AudioSource
from izunadsp import DSPServer

from core.music.queues import Queue


class Player:
    def __init__(self, voice_client: VoiceClient, queue: Queue, config: Dict = None):
        self.queue = queue
        self.voice_client = voice_client
        self.dsp_config = config
        self.server = DSPServer()
        for part, settings in config.items():
            for attribute, value in settings.items():
                self.server.config(part, attribute, value)

    def play(self, song: AudioSource, **kwargs):
        self.queue.add(song, **kwargs)

    def play_next(self):
        if self.queue:
            self.voice_client.play(self.queue.get(), after=self.play_next)
        else:
            self.voice_client.disconnect()
