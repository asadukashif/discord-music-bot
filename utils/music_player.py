import os
from time import gmtime, strftime, time
from typing import Dict, List

import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from discord.player import FFmpegPCMAudio
from spotipy.exceptions import SpotifyException
from youtube_dl.utils import DownloadError

from utils.data_object import DataObject

from .embeds import (BASIC, ERROR, basic_embed, common_embed,
                     get_song_now_embed, get_song_pause_embed,
                     get_song_resume_embed, get_song_start_embed,
                     get_song_stop_embed)
from .server_object import ServerObject
from .song import Song
from .spotify import SpotifySong, spotify_songs
from .time import Time
from .yt_config import YTDLSource, get_ffmpeg_options

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

        # Voice State of the author of the message
        voice_state = ctx.author.voice

        # Initializes the server object if it doesn't exist to be used for furthur things.
        init_server_object(ctx)
        # If the channel name to join is not provided
        if not channel:
            # If the bot is already in a channel then move it to the requested channel
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)
            # In case the name of the channel is not provided then join the Voice Channel of the caller (User sending the message)
            elif voice_state != None:
                channel = voice_state.channel
            # In case neither of the options are available then print the error message and return
            else:
                return await ctx.send(embed=common_embed(value="You must join a Voice Channel to provide a name", name="Error joining voice chat", color=ERROR))

        await ctx.send(embed=common_embed(name="Joining Voice Chat", value="Joined Voice Chat: " + str(channel)))
        # In case everything goes well and then the Voice Channel
        await channel.connect()

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, url: str = ""):
        """Plays from a song by keywords or url"""
        global objects  # Global objects that hold the ServerObjects for all the users.

        # Gets the server ID of the server
        server_id = str(ctx.guild.id)

        # Runs this function everytime the new song in queue is to be played
        def play_song():
            # Pops a song off of the queue
            node = objects[server_id].queue.pop()

            # If the queue is empty
            if node is None:
                return objects[server_id].reset()
            else:
                # Makes the player that will be played
                player = YTDLSource(FFmpegPCMAudio(node.filename, **get_ffmpeg_options(node.time)),
                                    data=node.data)
                ctx = node.ctx
                objects[server_id].current_song = player
                objects[server_id].current_ctx = ctx
                objects[server_id].curernt_node = node
                objects[server_id].current_time = Time(start=time(),
                                                       initial_seek=node.time)

                ctx.voice_client.play(
                    player, after=lambda e: play_song())

                # If the loop is enabled
                if objects[server_id].loop:
                    objects[server_id].queue.push_to_start(node)

        init_server_object(ctx)

        voice_state = ctx.author.voice
        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))
        if not url:
            return await ctx.send(embed=common_embed(value="You must provide the url or the name of the song", name="Error playing audio", color=ERROR))
        else:
            with ctx.typing():
                # If the bot needs to join the Voice Channel
                if not ctx.voice_client:
                    await voice_state.channel.connect()

                try:
                    # Gets and downloads the video and returns its filename on disk and data.
                    filename, data = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)
                except Exception:
                    await self.stop(ctx)
                    return await ctx.send(embed=common_embed(name="Error Playing Song",
                                                             value="The song couldn't be found. Try being a little more specific in the naming",
                                                             color=ERROR))

                # Pushes the song to the queue
                objects[server_id].queue.push(Song(ctx=ctx,
                                                   data=data,
                                                   time=0,
                                                   filename=data.get('filepath')))

                # Converts the data into an Object so that it's homogeneous with the other code and reused
                object = DataObject(data)
                await ctx.send(embed=get_song_start_embed(title=object.title,
                                                          url=object.url,
                                                          author=object.author,
                                                          thumbnail=object.thumbnail,
                                                          duration=object.duration,
                                                          pos_in_queue=objects[server_id].queue.get_size(
                                                          ),
                                                          requestee=(ctx.author.nick or ctx.author.display_name)))

                # If the song is being played for the first time.
                if objects[server_id].is_first:
                    objects[server_id].is_first = False

                    # Pops the value from the queue
                    node = objects[server_id].queue.pop()

                    # Generates the player
                    player = YTDLSource(FFmpegPCMAudio(node.filename, **get_ffmpeg_options(node.time)),
                                        data=node.data)
                    # Plays the song
                    ctx.voice_client.play(
                        player, after=lambda e: play_song())

                    objects[server_id].current_ctx = ctx
                    objects[server_id].current_song = player
                    objects[server_id].curernt_node = node
                    objects[server_id].current_time = Time(start=time())

    @ commands.command(aliases=['s'])
    async def skip(self, ctx: commands.Context, index: int = -1):
        """Skips the current song"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        init_server_object(ctx)

        # If the index is provided
        if (index != -1):
            # Checks if the index is not out of range and if not so then switches to that index else prints an error message
            if not objects[server_id].queue.skip_to(index):
                return await ctx.send(embed=common_embed(name="Error", value="The index provided is out of range", color=ERROR))

        """ Checks the following
            - If the bot is in a Voice Channel
            - If the Song is being played 
            - or is paused.
        """
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            objects[server_id].loop = False
            ctx.voice_client.stop()
            await ctx.send(embed=basic_embed(title="Skipping",
                                             desc=f"Skipping {objects[server_id].current_song.title}"))

    @ commands.command(aliases=['vol', 'v'])
    async def volume(self, ctx: commands.Context, volume: int = -1):
        """Changes the player's volume"""

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        # If the user is not in a Voice Channel
        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        # If the Bot is not in a Voice Channel
        if ctx.voice_client is None:
            return await ctx.send(embed=basic_embed("Not connected to a voice channel.", color=ERROR))

        init_server_object(ctx)

        # If the volume is not negative (or valid)
        if not volume < 0:
            # Chnages the Volume
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(embed=basic_embed(f"Changed volume to {volume}%"))
        # If the volume is invalid
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

        # If the Bot is already playing something
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send(embed=get_song_stop_embed(objects[server_id].current_song.title,
                                                     objects[server_id].current_song.thumbnail))

        # Resets the object and disconnects
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

        # If the user is not in a Voice Channel
        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        # Checks if the Song is playing
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            objects[server_id].current_time.paused_on = time()
            await ctx.send(embed=get_song_pause_embed(objects[server_id].current_song.title,
                                                      objects[server_id].current_song.thumbnail))

    @ commands.command(aliases=['res'])
    async def resume(self, ctx: commands.Context):
        """Resumes the audio"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        # If the user is not in a Voice Channel
        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        if ctx.voice_client != None and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            objects[server_id].current_time.paused_off = time()
            # Compensates for shit... will explain later
            objects[server_id].current_time.compensation += objects[server_id].current_time.paused_off - \
                objects[server_id].current_time.paused_on
            await ctx.send(embed=get_song_resume_embed(objects[server_id].current_song.title,
                                                       objects[server_id].current_song.thumbnail))

    @ commands.command(aliases=['q'])
    async def queue(self, ctx: commands.Context):
        """Displays the songs in queue"""
        global objects

        server_id = str(ctx.guild.id)
        init_server_object(ctx)

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        # If the user is not in a Voice Channel
        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        # Creates a basic embed
        embed = basic_embed("Queue", "The queue of the song is as follows")
        # If the bot in a Voice Channel and (it's either playing a song or is paused)
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            # If there exists a song that is being played
            if objects[server_id].current_song:
                # Sets the thumbnail of the currently playing song
                embed.set_thumbnail(
                    url=objects[server_id].current_song.thumbnail)
                # Adds field for the current song
                embed.add_field(name=f"Currently Playing **{objects[server_id].current_song.title}**",
                                value=objects[server_id].current_song.author)
                embed.add_field(name="Duration",
                                value=f"`{objects[server_id].current_song.duration}`", inline=False)
                index = 0   # A counter for counting all the values as list
                # Iterates over all the values
                for node in objects[server_id].queue.as_list():
                    index += 1
                    # Converts it into a DataObject
                    node = DataObject(node.data)
                    # Adds the field
                    embed.add_field(name=f'**{index}. {node.title}**',
                                    value=node.author)
                    embed.add_field(name="Duration",
                                    value=f"`{node.duration}`",
                                    inline=False)
            # If there is no current_song
            else:
                embed.add_field(name='Empty',
                                value="No more songs", inline=False)
        # If the music is not paused or not playing
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
        # If the time is negative
        if time < 0:
            return await ctx.send(embed=common_embed(value="Enter a valid time", name="Error Seeking", color=ERROR))
        # If the time is greater than the length of song
        if time >= song_duration:
            return await ctx.send(embed=common_embed(value="You can't seek past the Audio's length", name="Error Seeking", color=ERROR))
        # If the is not playing or is paused
        if not ctx.voice_client.is_playing():
            return await ctx.send(embed=common_embed(value="No song is currently playing", name="Error Seeking", color=ERROR))

        await ctx.send(embed=common_embed(value=f"Seeking to " + strftime("%H:%M:%S", gmtime(time)), name="Seeking ..."))

        current_node = objects[server_id].curernt_node
        # Setting the seek time
        current_node.time = time
        objects[server_id].queue.push_to_start(current_node)
        ctx.voice_client.stop()

    @ commands.command()
    async def now(self, ctx: commands.Context):
        """Shows the currently playing song"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        player = objects[server_id].current_song
        # If the current song exists
        if player:
            return await ctx.send(embed=get_song_now_embed(title=player.title,
                                                           url=player.url,
                                                           author=player.author,
                                                           thumnail=player.thumbnail,
                                                           duration=player.duration,
                                                           time_elapsed=objects[server_id].current_time,
                                                           total_duration=player.duration_secs))
        else:
            return await ctx.send(embed=common_embed(value="There's no song currently playing", name="Error getting the current song", color=ERROR))

    @ commands.command()
    async def replace(self, ctx: commands.Context, src_index: int = -1, dest_index: int = -1):
        """Interchanges the two song's indices"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        # If the indices are negative
        if src_index < 0 or dest_index < 0:
            return await ctx.send(embed=common_embed(value="Provide valid indices", name="Error playing audio", color=ERROR))

        # If the replacing process was successful
        if objects[server_id].queue.replace(src_index, dest_index):
            return await ctx.send(embed=common_embed(value=f"The indices {src_index} and {dest_index} were replaced successfully", name="Song switched"))

        return await ctx.send(embed=common_embed(value="An unknown error has occurred", name="Error playing audio", color=ERROR))

    @ commands.command(aliases=['del'])
    async def delete(self, ctx: commands.Context, index: int = -1):
        """Deletes a particular index from the queue"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        # If the index is incorrect (0 or negative)
        if index <= 0:
            return await ctx.send(embed=common_embed(value="Provide valid index", name="Error deleting song", color=ERROR))

        # If the deletion was successful
        if objects[server_id].queue.delete(index):
            return await ctx.send(embed=common_embed(value=f"The song at index {index} has been deleted successfully", name="Song Deleted"))

        return await ctx.send(embed=common_embed(value="An unknown error has occurred", name="Error playing audio", color=ERROR))

    @ commands.command(aliases=[''])
    async def loop(self, ctx: commands.Context):
        """Loops to the current current"""
        global objects

        server_id = str(ctx.guild.id)
        voice_state = ctx.author.voice

        if not voice_state:
            return await ctx.send(embed=common_embed(value="You must join a Voice Channel first", name="Error playing audio", color=ERROR))

        # Toggles the loop
        objects[server_id].loop = not objects[server_id].loop

        # Adds the current song to the start of the queue
        if objects[server_id].loop:
            objects[server_id].queue.push_to_start(
                objects[server_id].curernt_node)

        return await ctx.send(embed=common_embed(name="Loop Status Changed", value="The loop is currently %s"
                                                 "activated" if objects[server_id].loop else "deactivated"))

    @ commands.command(aliases=['qspotify'])
    async def queuespotify(self, ctx: commands.Context, limit: int = 5, playlist_code: str = ""):
        """Gets the songs from our spotify playlist"""
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
