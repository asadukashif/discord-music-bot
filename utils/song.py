import discord
from discord.ext import commands


class Song():
    def __init__(self, ctx: commands.Context, data: dict, time: int, filename: str) -> None:
        self.ctx = ctx
        self.data = data
        self.time = time
        self.filename = filename
