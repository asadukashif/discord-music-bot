import dotenv

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from typing import *

dotenv.load_dotenv("../.env")


class Song():
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


def spotify_songs(spotify_playlist: str = "spotify:playlist:5w9MQEn7bjYGIBMBGkwMfK", limit: int = 10) -> List[Song]:
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_SECRET'),
                                              client_secret=os.getenv('SPOTIFY_CLIENT_ID')))
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
        song = Song(track_name, artists)
        songs.append(song)
    return songs
