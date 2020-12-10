import dotenv

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from typing import *
import random

dotenv.load_dotenv("../.env")


class SpotifySong():
    def __init__(self, song_name: str, artists: List[str]) -> None:
        self.song_name = song_name
        self.artists = artists

    def format_artists(self) -> str:
        if len(self.artists) == 1:
            return self.artists[0]
        else:
            string = ""
            for artist in self.artists:
                string += artist + " and "

            if string.endswith("and "):
                string = string[:-4]

            return string

    def __repr__(self) -> str:
        return f"{self.song_name} by {self.format_artists()}"


def spotify_songs(spotify_playlist: str = "spotify:playlist:5w9MQEn7bjYGIBMBGkwMfK", limit: int = 5) -> List[SpotifySong]:
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                                              client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')))
    tracks = sp.playlist_tracks(
        spotify_playlist, limit=limit)

    songs = []
    for track_object in tracks.get('items', []):
        track = track_object.get('track')

        track_name = track.get('name')
        artist_object = track.get('artists')
        artists = []
        for artist in artist_object:
            artists.append(artist.get('name'))
        song = SpotifySong(track_name, artists)
        songs.append(song)

    numbers_drawn: List[int] = []
    songs_to_send: List[SpotifySong] = []

    for i in range(limit):
        while True:
            rand_index = random.randint(0, len(songs))
            if rand_index not in numbers_drawn:
                numbers_drawn.append(rand_index)
                break

        songs_to_send.append(songs[rand_index])

    return songs_to_send
