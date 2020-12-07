import discord
from discord.ext import commands

from .queue import Queue
from .yt_config import YTDLSource


class ServerObject():
    def __init__(self, current_ctx: commands.Context = None, current_song: YTDLSource = None) -> None:
        self.queue = Queue()
        self.current_song = current_song
        self.current_ctx = current_ctx
        self.curernt_node = {}
        self.is_first = True
        self.loop = False

    def reset(self):
        self.queue = Queue()
        self.current_song = None
        self.is_first = True
