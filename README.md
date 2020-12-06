# Discord Music Bot
This a music bot that allows the users in a channel to request songs from YouTube by either keywords or URL directly. The music can then be manipulated by commands.
___

## Installation
To download you need the following 
- [FFMPEG](https://ffmpeg.org/download.html)
- [Python](https://github.com/ytdl-org/youtube-dl)
- Install the packages in `requirements.txt` by
    
        pip install -r requirements.txt 

- Set the following environment
  - `DISCORD_KEY`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_CLIENT_ID`
- Run using 

        python bot.py 
___

## Gallery
- ### Join
    ![join](images/join.png)
___
- ### Play
    ![play](images/play.png)
___
- ### Pause
    ![pause](images/pause.png)
___
- ### Resume
    ![Resume](images/Resume.png)
___
- ### Queue
    ![Queue](images/Queue.png)
___
- ### Now
    ![Now](images/Now.png)
___
- ### Skip
    ![Skip](images/Skip.png)
___
- ### Volume
    ![Volume](images/Volume.png)
___
- ### Seek
    ![Seek](images/Seek.png)

___

## Commands
The following commands can be used with either `!` or `.`
- `join` : Joins a voice channel where the caller resides or a specific channel if the name is provided as an argument.
- `play` : Plays a particular song from the keywords or URL entered or if already playing adds it to the queue.
- `pause` : Pauses a the currently playing.
- `resume` : Resumes a the currently playing.
- `now` : Shows the currently playing song.
- `seek` : Move to a certain second-point of the song.
- `skip` : Skips the current song and moves to the next one in queue or if provided the song index, skips to that song directly.
- `volume` : Shows the current volume or if provided a certain value, changes the volume to that value (max is 200).
- `queue` : Displays the current queue.
- `shuffle` : Randomly shuffles the queue.
- `clear` : Clears the queue.
- `stop` : Stops the currently playing song and leaves the voice channel.
- `queuespotify` : Provided the quantity and URL of your spotify playlist, can fetch that quantity of songs from your playlist and add them to queue.
___

## TechStack
The tech stack used in stated below.
- [Python](https://github.com/ytdl-org/youtube-dl)
- [Discord Rewrite](https://github.com/Rapptz/discord.py)
- [Spotipy](https://github.com/plamere/spotipy)
- [YouTube DL](https://github.com/ytdl-org/youtube-dl)
- [FFMPEG](https://ffmpeg.org/)

____