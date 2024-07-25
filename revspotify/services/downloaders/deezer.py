import requests
from bs4 import BeautifulSoup
import json
from pydeezer import Deezer
from pydeezer.exceptions import LoginError
from pydeezer.constants import track_formats
import os

from services.response import Response
from services.utils import clean_filename
from logger import Logger

logger = Logger("DeezerService")

USED_ARLS_FILE = "data/deezer_used_arls.json"
DOWNLOAD_DIR = "data/downloads"


class ARLManager:
    def __init__(self):
        logger.info("Initializing ARLManager")
        self.used_arls = self.load_used_arls()

    def load_used_arls(self):
        logger.info("Loading used ARLs")
        if os.path.exists(USED_ARLS_FILE):
            with open(USED_ARLS_FILE, "r") as file:
                return json.load(file)
        return []

    def save_used_arls(self):
        logger.info("Saving used ARLs")
        with open(USED_ARLS_FILE, "w") as file:
            json.dump(self.used_arls, file)

    def gather_arls(self):
        logger.info("Gathering ARLs")
        url = "https://rentry.org/firehawk52#deezer-arls"
        arls = []
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.find_all(class_="ntable")

            for element in elements:
                rows = element.find_all("tr")
                for row in rows[1:]:
                    arl = [column.text for column in row.find_all("td")[1:-1]][-1]
                    if arl not in self.used_arls:
                        arls.append(arl)
        else:
            logger.error(f"Failed to gather ARLs, status code: {response.status_code}")

        return arls[::-1]

    def validate_arl(self, arl):
        logger.info(f"Validating ARL: {arl}")
        try:
            deezer = Deezer(arl=arl)
            deezer.user  # Attempt to access user info to validate ARL
            return True
        except LoginError as e:
            logger.error(f"LoginError during ARL validation: {e}")
            return False

    def get_valid_arl(self):
        logger.info("Getting a valid ARL")
        arls = self.gather_arls()

        for arl in arls:
            if self.validate_arl(arl):
                logger.info(f"Found valid ARL: {arl}")
                return arl
            else:
                self.used_arls.append(arl)
                self.save_used_arls()

        logger.error("No valid ARL found")
        return None


class DeezerService:
    def __init__(self):
        logger.info("Initializing DeezerService")
        self.arl_manager = ARLManager()
        self.used_arls = set()
        self.update_arl()

    def update_arl(self):
        logger.info("Updating ARL")
        arl = self.arl_manager.get_valid_arl()
        if arl is None:
            logger.error("No valid ARL found")
            return Response(error="No valid ARL found", service="deezer")
        self.used_arls.add(arl)
        self.arl = arl
        self.deezer = Deezer(arl=self.arl)
        logger.info("ARL updated successfully")

    def get_user_info(self):
        logger.info("Fetching user info")
        if not self.is_arl_valid():
            logger.warning("ARL is not valid, updating ARL")
            self.update_arl()
        return self.deezer.user

    def search_tracks(self, query):
        logger.info(f"Searching tracks for query: {query}")
        return self.deezer.search_tracks(query)

    def search_and_download_track(self, query, duration_in_seconds):
        logger.info(f"Searching and downloading track for query: {query}, duration: {duration_in_seconds}")
        search_results = self.search_tracks(query)
        for track in search_results:
            if abs(track["duration"] - duration_in_seconds) <= 5:  # Allowing a 5-second difference
                track_id = track["id"]
                download_response = self.download_track(track_id)
                return download_response
        logger.warning("No matching track found")
        return Response(error="No matching track found.", service="deezer")

    def download_track(self, track_id):
        logger.info(f"Downloading track with ID: {track_id}")
        try:
            track = self.deezer.get_track(track_id)
            if not track:
                logger.error("Track not found")
                return Response(error="Track not found", service="deezer")

            # Download the track
            filename = f"{track['info']['DATA']['ART_NAME']} - {track['info']['DATA']['SNG_TITLE']}.mp3"
            filename = clean_filename(filename)
            track["download"](
                DOWNLOAD_DIR,
                quality=track_formats.MP3_320,
                with_lyrics=False,
                filename=filename,
            )

            # check if the file exists
            if os.path.exists(f"{DOWNLOAD_DIR}/{filename}"):
                logger.info("Track downloaded successfully")
                return Response(
                    music_address=f"{DOWNLOAD_DIR}/{filename}", service="deezer"
                )
            logger.error("Failed to download track")
            return Response(error="Failed to download track", service="deezer")

        except Exception as e:
            logger.error(f"Error in download_track: {e}")
            return Response(error=f"Error in download_track: {e}", service="deezer")