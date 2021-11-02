import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from youtube_search import YoutubeSearch
import yt_dlp
import eyed3.id3
import eyed3
import re
from os import remove


class Spotify:
    def __init__(self):
        self.client_id = "a145db3dcd564b9592dacf10649e4ed5"
        self.client_secret = "389614e1ec874f17b8c99511c7baa2f6"
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
        )


    def convert_youtube_time_duration_to_seconds(self, time_duration):
        time_duration_splitted = time_duration.split(":")
        seconds = 0
        print(time_duration_splitted)
        print(time_duration)
        if len(time_duration_splitted) == 1:
            seconds += int(time_duration_splitted[-1])
        elif len(time_duration_splitted) == 2:
            seconds += int(time_duration_splitted[-1])
            seconds += int(time_duration_splitted[-2]) * 60
        elif len(time_duration_splitted) == 3:
            seconds += int(time_duration_splitted[-1])
            seconds += int(time_duration_splitted[-2]) * 60
            seconds += int(time_duration_splitted[-3]) * 60 * 60
        elif len(time_duration_splitted) == 4:
            seconds += int(time_duration_splitted[-1])
            seconds += int(time_duration_splitted[-2]) * 60
            seconds += int(time_duration_splitted[-3]) * 60 * 60
            seconds += int(time_duration_splitted[-4]) * 60 * 60 * 60

        return seconds

    def download_track(self, link):
        results = self.spotify.track(link)
        song = results["name"]
        artist = results["artists"][0]["name"]
        YTSEARCH = str(song + " " + artist)
        artistfinder = results["artists"]
        tracknum = results["track_number"]
        album = results["album"]["name"]
        realese_date = int(results["album"]["release_date"][:4])

        if len(artistfinder) > 1:
            fetures = "( Ft."
            for lomi in range(0, len(artistfinder)):
                try:
                    if lomi < len(artistfinder) - 2:
                        artistft = artistfinder[lomi + 1]["name"] + ", "
                        fetures += artistft
                    else:
                        artistft = artistfinder[lomi + 1]["name"] + ")"
                        fetures += artistft
                except:
                    pass
        else:
            fetures = ""

        millis = results["duration_ms"]
        millis = int(millis)
        spotify_track_seconds = (millis / 1000)

        trackname = song + fetures
        # Download Cover
        response = requests.get(results["album"]["images"][0]["url"])
        DIRCOVER = "static/covers/" + trackname + ".png"
        file = open(DIRCOVER, "wb")
        file.write(response.content)
        file.close()
        # search for music on youtube
        results = list(YoutubeSearch(str(YTSEARCH)).to_dict())
        LINKASLI = ""
        for URLSSS in results:
            timeyt = URLSSS["duration"]
            youtube_video_seconds = self.convert_youtube_time_duration_to_seconds(timeyt)
            if abs(youtube_video_seconds - spotify_track_seconds) <= 4:
                LINKASLI = URLSSS["url_suffix"]
                break
        if LINKASLI == "":
            return {"error": f"Sorry, there is no match for '{song}'"}

        YTLINK = str("https://www.youtube.com/" + LINKASLI)
        options = {
            # PERMANENT options
            "format": "bestaudio/best",
            "keepvideo": False,
            "outtmpl": f"static/songs/{trackname}.*",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }

        with yt_dlp.YoutubeDL(options) as mp3:
            mp3.download([YTLINK])

        aud = eyed3.load(f"static/songs/{trackname}.mp3")
        aud.tag.artist = artist
        aud.tag.album = album
        aud.tag.album_artist = artist
        aud.tag.title = trackname
        aud.tag.track_num = tracknum
        aud.tag.year = realese_date
        aud.tag.images.set(
            3, open(f"static/covers/{trackname}.png", "rb").read(), "image/png"
        )
        aud.tag.save()
        return {"cover_path": f"static/covers/{trackname}.png", "music_path": f"static/songs/{trackname}.mp3", "name": trackname, "error": None}

    def album(self, link):
        results = self.spotify.album_tracks(link)
        tracks = list()
        for track in results["items"]:
            tracks.append(track["external_urls"]["spotify"])

        return tracks


    def top_tracks_artist(self, link):
        results = self.spotify.artist_top_tracks(link)
        top_tracks = list()
        for top_track in results["tracks"]:
            top_tracks.append(top_track["external_urls"]["spotify"])
        return top_tracks


    def playlist(self, link):
        results = self.spotify.playlist_tracks(link)
        playlist_tracks = list()
        for track in results["items"]:
            playlist_tracks.append(track["track"]["external_urls"]["spotify"])
        return playlist_tracks

    def analyse_spotify_link(self, text):
        spotify_regex = "(\/(track|playlist|artist|album|spotify|download)@revspotifybot )?(https?://)?(www\.)?(open.spotify)\.(com)/(track|album|artist|playlist)/?([^&=%\?]{22}).+"
        spotify_regex_match = re.findall(spotify_regex, text)
        if spotify_regex_match == list():
            return False
        spotify_link_type = spotify_regex_match[0][-2]
        link = f"https://open.spotify.com/{spotify_link_type}/{spotify_regex_match[0][-1]}"

        return {"spotify_link_type": spotify_link_type, "link": link}
            

class File:
    def remove_file(self, path):
        remove(path)
        return True