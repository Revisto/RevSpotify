import requests
from bs4 import BeautifulSoup
import json
from pydeezer import Deezer
from pydeezer.exceptions import LoginError
from pydeezer.constants import track_formats
import os

from services.response import Response
from services.utils import clean_filename

USED_ARLS_FILE = 'data/deezer_used_arls.json'
DOWNLOAD_DIR = 'data/downloads'

class ARLManager:
    def __init__(self):
        self.used_arls = self.load_used_arls()

    def load_used_arls(self):
        if os.path.exists(USED_ARLS_FILE):
            with open(USED_ARLS_FILE, 'r') as file:
                return json.load(file)
        return []

    def save_used_arls(self):
        with open(USED_ARLS_FILE, 'w') as file:
            json.dump(self.used_arls, file)

    def gather_arls(self):
        url = 'https://rentry.org/firehawk52#deezer-arls'
        arls = []
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.find_all(class_='ntable')
        
        for element in elements:
            rows = element.find_all('tr')
            for row in rows[1:]:
                arl = [column.text for column in row.find_all('td')[1:-1]][-1]
                if arl not in self.used_arls:
                    arls.append(arl)

        return arls[::-1]

    def validate_arl(self, arl):
        try:
            deezer = Deezer(arl=arl)
            deezer.user  # Attempt to access user info to validate ARL
            return True
        except LoginError:
            return False

    def get_valid_arl(self):
        arls = self.gather_arls()
        
        for arl in arls:
            if self.validate_arl(arl):
                return arl
            else:
                self.used_arls.append(arl)
                self.save_used_arls()
        
        return None

class DeezerService():
    def __init__(self):
        self.arl_manager = ARLManager()
        self.used_arls = set()
        self.update_arl()

    def update_arl(self):
        arl = self.arl_manager.get_valid_arl()
        if arl is None:
            return Response(error="No valid ARL found", service='deezer')
        self.used_arls.add(arl)
        self.arl = arl
        self.deezer = Deezer(arl=self.arl)

    def get_user_info(self):
        if not self.is_arl_valid():
            self.update_arl()
        return self.deezer.user
    
    def search_tracks(self, query):
        return self.deezer.search_tracks(query)
    
    def search_and_download_track(self, query, duration_in_seconds):
        search_results = self.search_tracks(query)
        for track in search_results:
            if abs(track['duration'] - duration_in_seconds) <= 5:  # Allowing a 5-second difference
                track_id = track['id']
                download_response = self.download_track(track_id)
                return download_response
        return Response(error="No matching track found.", service='deezer')
    
    def download_track(self, track_id):
        try:
            track = self.deezer.get_track(track_id)
            if not track:
                return Response(error="Track not found", service='deezer')

            # Download the track
            filename = f"{track['info']['DATA']['ART_NAME']} - {track['info']['DATA']['SNG_TITLE']}.mp3"
            filename = clean_filename(filename)
            track["download"](DOWNLOAD_DIR, quality=track_formats.MP3_320, with_lyrics=False, filename=filename)

            # check if the file exists
            if os.path.exists(f"{DOWNLOAD_DIR}/{filename}"):
                return Response(music_address=f"{DOWNLOAD_DIR}/{filename}", service='deezer')
            return Response(error="Failed to download track", service='deezer')

        except Exception as e:
            return Response(error=f"Error in download_track: {e}", service='deezer')