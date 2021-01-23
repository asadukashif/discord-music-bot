import discord
from discord.ext import commands

from .queue import Queue
from .song import Song
from .yt_config import YTDLSource


class ServerObject():
    def __init__(self, current_ctx: commands.Context = None, current_song: YTDLSource = None) -> None:
        self.queue = Queue()
        self.current_song = current_song
        self.current_ctx = current_ctx
        self.current_node = Song
        self.is_first = True
        self.loop = False
        self.current_starttime = 0.0

    def reset(self, clear_queue: bool = True):
        self.queue.clear() if clear_queue else ...
        self.current_song = None
        self.is_first = True
        self.loop = False
        self.current_starttime = 0.0
