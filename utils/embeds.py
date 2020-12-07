from typing import Tuple
import discord
from discord.embeds import Embed


START = (0, 242, 218)
RESUME = (7, 230, 40)
PAUSE = (252, 177, 3)
STOP = (230, 48, 7)

BASIC = (199, 2, 189)
ERROR = (224, 0, 0)


def get_song_start_embed(title: str = "",
                         requestee: str = "",
                         url: str = "",
                         author: str = "",
                         duration: str = "",
                         pos_in_queue: int = 1,
                         thumbnail: str = "") -> discord.embeds.Embed:

    embed = Embed(
        color=discord.Colour.from_rgb(*START),
        title=f"Added to queue",
        description=f"Playing {title}",
        url=url
    )
    embed.set_author(name=author, icon_url=thumbnail) \
        .set_thumbnail(url=thumbnail) \
        .set_footer(
        text=f"This song was requested by {requestee}" if requestee else "") \
        .add_field(name='Duration', value=duration, inline=True) \
        .add_field(name='Position in Queue', value=pos_in_queue, inline=True)

    return embed


def get_song_now_embed(title: str = "",
                       url: str = "",
                       author: str = "",
                       duration: str = "",
                       thumnail: str = "") -> discord.embeds.Embed:

    embed = Embed(
        color=discord.Colour.from_rgb(*START),
        title=f"Now playing",
        description=f"{title}",
        url=url
    )
    embed.set_author(name=author, icon_url=thumnail) \
        .set_thumbnail(url=thumnail) \
        .add_field(name='Duration', value=duration, inline=True)

    return embed


def get_song_pause_embed(title: str,
                         thumbnail: str = "") -> discord.embeds.Embed:
    return Embed(
        color=discord.Colour.from_rgb(*PAUSE),
        title=f"Paused",
        description=f"Were Playing {title}",
    ).set_thumbnail(url=thumbnail)


def get_song_resume_embed(title: str,
                          thumbnail: str = "") -> discord.embeds.Embed:
    return Embed(
        color=discord.Colour.from_rgb(*RESUME),
        title=f"Resumed",
        description=f"Now Playing {title}",
    ).set_thumbnail(url=thumbnail)


def get_song_stop_embed(title: str,
                        thumbnail:str="") -> discord.embeds.Embed:
    return Embed(
        color=discord.Colour.from_rgb(*STOP),
        title=f"Stopped",
        description=f"Were Playing {title}",
    ).set_thumbnail(url=thumbnail)


def basic_embed(title: str = "", desc: str = "", color: Tuple = BASIC) -> discord.embeds.Embed:
    return Embed(title=title, description=desc, color=discord.Colour.from_rgb(*color))


def common_embed(color: Tuple = BASIC, name: str = "", value: str = ""):
    return basic_embed(color=color).add_field(name=name, value=value)
