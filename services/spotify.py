import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config.config import Config
from services.utils import Singleton


class SpotifyService(metaclass=Singleton):
    def __init__(self):
        self.client_id = Config.SPOTIFY_CLIENT_ID
        self.client_secret = Config.SPOTIFY_CLIENT_SECRET
        self.client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.client_secret
        )
        self.sp = spotipy.Spotify(
            client_credentials_manager=self.client_credentials_manager
        )

    def search_track(self, query):
        results = self.sp.search(q=query, type="track")
        return results

    def get_track_info(self, track_id):
        track_info = self.sp.track(track_id)
        return track_info

    def get_playlist_info(self, playlist_id):
        playlist_info = self.sp.playlist(playlist_id)
        return playlist_info

    def get_album_info(self, album_id):
        album_info = self.sp.album(album_id)
        return album_info
