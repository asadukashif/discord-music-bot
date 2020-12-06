import os
from time import gmtime, strftime
from typing import Dict, List

import discord
from discord.ext import commands
from discord.player import FFmpegPCMAudio
from spotipy.exceptions import SpotifyException

from .embeds import (BASIC, ERROR, basic_embed, common_embed,
                     get_song_now_embed, get_song_pause_embed,
                     get_song_resume_embed, get_song_start_embed,
                     get_song_stop_embed)
from .server_object import ServerObject
from .yt_config import YTDLSource, get_ffmpeg_options
from .spotify import spotify_songs, Song
# Holds server objects
objects: Dict[str, ServerObject] = {}


def init_server_object(ctx: commands.Context):
    global objects

    server_id = str(ctx.guild.id)

    if objects.get(server_id, None) is None:
        objects[server_id] = ServerObject(current_ctx=ctx)


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['j'])
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Joins a voice channel if specified else joins the one in which the caller resides"""
        voice_state = ctx.author.voice

        init_server_object(ctx)
        if not channel:
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)
            elif voice_state != None:
                channel = voice_state.channel
            else:
                return await ctx.send(embed=common_embed(value="You must join a Voice Channel to provide a name", name="Error joining voice chat", color=ERROR))

        await ctx.send(embed=common_embed(name="Joining Voice Chat", value="Joined Voice Chat: " + str(channel)))
        await channel.connect()

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, url: str = "", is_seek: bool = False, seek_filename: str = "", seek_data: object = None, seek_time: int = 0):
        """Plays from a song by keywords or url"""
        global objects

        server_id = str(ctx.guild.id)

        def play_song():
            node = objects[server_id].queue.pop()

            if node is None:
                return objects[server_id].reset()
            else:
                player = node.get('player')
                objects[server_id].current_song = player
                ctx = node.get('ctx')
                objects[server_id].current_ctx = ctx

                ctx.voice_client.play(
                    player, after=lambda e: play_song())

        init_server_object(ctx)

        voice_state = ctx.author.voice
        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))
        if not url and not is_seek:
            return await ctx.send(embed=common_embed(value="You must provide the url or the name of the song", name="Error playing audio", color=ERROR))
        else:
            with ctx.typing():
                if not ctx.voice_client:
                    await voice_state.channel.connect()

                if is_seek:
                    filename = seek_filename
                    data = seek_data
                    objects[server_id].is_first = True
                else:
                    filename, data = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)

                player = YTDLSource(FFmpegPCMAudio(filename, **get_ffmpeg_options(seek_time)),
                                    data=data)

                if not is_seek:
                    await ctx.send(embed=get_song_start_embed(title=player.title,
                                                              url=player.url,
                                                              author=player.artist,
                                                              thumbnail_obj=player.thumbnail_obj,
                                                              duration=player.duration, requestee=(
                                                                  ctx.author.nick or ctx.author.display_name)))
                if is_seek:
                    objects[server_id].queue.push_to_start({
                        'player': player, 'ctx': ctx})
                else:
                    objects[server_id].queue.push({
                        'player': player, 'ctx': ctx})

                if objects[server_id].is_first:
                    objects[server_id].is_first = False

                    node = objects[server_id].queue.pop()

                    if is_seek:
                        ctx.voice_client.stop()

                    ctx.voice_client.play(
                        node['player'], after=lambda e: play_song())

                    objects[server_id].current_ctx = ctx
                    objects[server_id].current_song = node['player']

    @ commands.command(aliases=['s'])
    async def skip(self, ctx: commands.Context, index: int = -1):
        """Skips the current song"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if (not voice_state):
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        init_server_object(ctx)

        if (index != -1):
            if not objects[server_id].queue.skip_to(index):
                return await ctx.send(embed=common_embed(name="Error", value="The index provided is out of range", color=ERROR))

        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send(embed=basic_embed(title="Skipping",
                                             desc=f"Skipping {objects[server_id].current_song.title}"))

    @ commands.command(aliases=['vol', 'v'])
    async def volume(self, ctx: commands.Context, volume: int = -1):
        """Changes the player's volume"""

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        if ctx.voice_client is None:
            return await ctx.send(embed=basic_embed("Not connected to a voice channel.", color=ERROR))

        init_server_object(ctx)

        if not volume < 0:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(embed=basic_embed(f"Changed volume to {volume}%"))
        else:
            await ctx.send(embed=common_embed(name="Volume Level", value="The current volume is " + str(ctx.voice_client.source.volume * 100)))

    @ commands.command(aliases=[])
    async def stop(self, ctx: commands.Context):
        """Stops and disconnects the bot from voice"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        init_server_object(ctx)

        await ctx.send(embed=get_song_stop_embed(objects[server_id].current_song.title,
                                                 objects[server_id].current_song.thumbnail_obj))

        ctx.voice_client.stop() if ctx.voice_client else ...
        objects[server_id].reset()
        await ctx.voice_client.disconnect()

    @ commands.command(aliases=['pau'])
    async def pause(self, ctx: commands.Context):
        """Pauses the audio"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        init_server_object(ctx)

        if ctx.voice_client != None and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(embed=get_song_pause_embed(objects[server_id].current_song.title,
                                                      objects[server_id].current_song.thumbnail_obj))

    @ commands.command(aliases=['res'])
    async def resume(self, ctx: commands.Context):
        """Resumes the audio"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        if ctx.voice_client != None and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(embed=get_song_resume_embed(objects[server_id].current_song.title,
                                                       objects[server_id].current_song.thumbnail_obj))

    @ commands.command(aliases=['q'])
    async def queue(self, ctx: commands.Context):
        """Displays the songs in queue"""
        global objects

        server_id = str(ctx.guild.id)
        init_server_object(ctx)

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        embed = basic_embed("Queue", "The queue of the song is as follows")
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            if objects[server_id].current_song:
                embed.set_thumbnail(
                    url=objects[server_id].current_song.thumbnail_obj.get('url'))
                embed.add_field(
                    name=f"Currently Playing {objects[server_id].current_song.title}...", value=objects[server_id].current_song.artist)
                embed.add_field(name="Duration",
                                value=objects[server_id].current_song.duration, inline=False)
                index = 0
                for node in objects[server_id].queue.as_list():
                    index += 1
                    node = node.get('player')
                    embed.add_field(name=f'{index}. {node.title}',
                                    value=node.artist, )
                    embed.add_field(name="Duration",
                                    value=node.duration, inline=False)

            else:
                embed.add_field(name='Empty',
                                value="No more songs", inline=False)
        else:
            embed.add_field(name='Empty',
                            value="No more songs", inline=False)

        await ctx.send(embed=embed)

    @ commands.command(aliases=[])
    async def shuffle(self, ctx: commands.Context):
        """Randomly shuffles the queue."""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        init_server_object(ctx)

        objects[server_id].queue.shuffle()
        await ctx.send(embed=common_embed(name="Shuffle Complete", value="The new queue is ..."))
        await self.queue(ctx)

    @ commands.command()
    async def clear(self, ctx: commands.Context):
        """Clears the queue"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        objects[server_id].queue.clear()
        await ctx.send(embed=common_embed(value="The queue has been cleared", name="Queue Cleared"))

    @ commands.command()
    async def seek(self, ctx: commands.Context, *, time: int = -1):
        """Skips to a certain second on the audio"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        current_song = objects[server_id].current_song
        song_duration = current_song.duration_secs
        song_url = current_song.url
        if (time < 0):
            return await ctx.send(embed=common_embed(value="Enter a valid time", name="Error Seeking", color=ERROR))
        if (time >= song_duration):
            return await ctx.send(embed=common_embed(value="You can't seek past the Audio's length", name="Error Seeking", color=ERROR))
        if (not ctx.voice_client.is_playing()):
            return await ctx.send(embed=common_embed(value="No song is currently playing", name="Error Seeking", color=ERROR))

        await ctx.send(embed=common_embed(value=f"Seeking to " + strftime("%M:%S", gmtime(time)), name="Seeking ..."))

        await self.play(ctx,
                        is_seek=True,
                        seek_data=current_song.data,
                        seek_filename=current_song.filepath,
                        seek_time=time)

    @ commands.command()
    async def now(self, ctx: commands.Context):
        """Shows the currently playing song"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        player = objects[server_id].current_song
        if player:
            return await ctx.send(embed=get_song_now_embed(title=player.title,
                                                           url=player.url,
                                                           author=player.artist,
                                                           thumbnail_obj=player.thumbnail_obj,
                                                           duration=player.duration))
        else:
            return await ctx.send(embed=common_embed(value="There's no song currently playing", name="Error getting the current song", color=ERROR))

    @ commands.command(aliases=['qspotify'])
    async def queuespotify(self, ctx: commands.Context, limit: int = 10, playlist_code: str = ""):
        try:
            if playlist_code:
                songs = spotify_songs(playlist_code, limit)
            else:
                songs = spotify_songs(limit=limit)
        except SpotifyException as e:
            ctx.send(embed=common_embed(
                name="Spotify Error", value=str(e), color=ERROR))

        for song in songs:
            await self.play(ctx, url=str(song))
