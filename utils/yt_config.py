import asyncio
import os
from time import gmtime, strftime

import discord
import youtube_dl

from .data_object import DataObject

ytdl_format_options = {
    'format': 'bestaudio/flac',
    'outtmpl': 'songs/%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        object = DataObject(data)
        self.data = data
        self.title = object.title
        self.url = object.url
        self.song_id = object.song_id
        self.author = object.author
        self.thumbnail = object.thumbnail
        self.duration_secs = object.duration_secs
        self.filepath = object.filepath
        self.duration = object.duration

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream: bool = False) -> list:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        data['filepath'] = filename

        return filename, data


def get_ffmpeg_options(time_start: int = 0) -> dict:
    return {
        'options': f'-vn -ss {time_start}'
    }
