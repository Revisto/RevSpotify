import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config.config import Config
from services.utils import Singleton
from logger import Logger

class SpotifyService(metaclass=Singleton):
    def __init__(self):
        self.logger = Logger("SpotifyService")
        self.logger.info("Initializing SpotifyService")
        self.client_id = Config.SPOTIFY_CLIENT_ID
        self.client_secret = Config.SPOTIFY_CLIENT_SECRET
        self.client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.client_secret
        )
        self.sp = spotipy.Spotify(
            client_credentials_manager=self.client_credentials_manager
        )
        self.logger.info("SpotifyService initialized successfully")

    def search_track(self, query):
        self.logger.info(f"Searching for track: {query}")
        results = self.sp.search(q=query, type="track")
        self.logger.info(f"Search completed for query: {query}")
        return results

    def get_track_info(self, track_id):
        self.logger.info(f"Fetching track info for ID: {track_id}")
        track_info = self.sp.track(track_id)
        self.logger.info(f"Track info fetched for ID: {track_id}")
        return track_info

    def get_playlist_info(self, playlist_id):
        self.logger.info(f"Fetching playlist info for ID: {playlist_id}")
        playlist_info = self.sp.playlist(playlist_id)
        self.logger.info(f"Playlist info fetched for ID: {playlist_id}")
        return playlist_info

    def get_album_info(self, album_id):
        self.logger.info(f"Fetching album info for ID: {album_id}")
        album_info = self.sp.album(album_id)
        self.logger.info(f"Album info fetched for ID: {album_id}")
        return album_info

    def get_artist_info(self, artist_id):
        self.logger.info(f"Fetching artist info for ID: {artist_id}")
        artist_info = self.sp.artist(artist_id)
        artist_top_tracks = self.sp.artist_top_tracks(artist_id)
        artist_info["top_tracks"] = artist_top_tracks["tracks"]
        self.logger.info(f"Artist info fetched for ID: {artist_id}")
        return artist_info