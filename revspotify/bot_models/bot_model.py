import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from youtube_search import YoutubeSearch
import yt_dlp
import eyed3.id3
import eyed3
import re
 
from time import strftime, gmtime
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
        time_duration_splitted.reverse()
        seconds = 0

        for i in range(len(time_duration_splitted)):
            seconds += 60 ** (i) * int(time_duration_splitted[i])

        return seconds

    def download_track(self, link):
        results = self.spotify.track(link)
        deezer_results = Deezer().search_and_download_track(results)
        if deezer_results["error"] is None:
            return deezer_results
        
        youtube_results = self.download_track_from_youtube(results)
        return youtube_results

    def download_track_from_youtube(self, results):
        song = results["name"]
        artist = results["artists"][0]["name"]
        YTSEARCH = str(song + " " + artist)
        artistfinder = results["artists"]
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
        spotify_track_seconds = millis / 1000

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
            youtube_video_seconds = self.convert_youtube_time_duration_to_seconds(
                timeyt
            )
            if abs(youtube_video_seconds - spotify_track_seconds) <= 4:
                LINKASLI = URLSSS["url_suffix"]
                break
        if LINKASLI == "":
            return {"error": {"song_name": song}}

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
        aud.tag.year = realese_date
        aud.tag.images.set(
            3, open(f"static/covers/{trackname}.png", "rb").read(), "image/png"
        )
        aud.tag.save()
        return {
            "cover_path": f"static/covers/{trackname}.png",
            "music_path": f"static/songs/{trackname}.mp3",
            "name": trackname,
            "error": None,
        }

    def search_track(self, text):
        """ Not working, need to fix """

        results = self.spotify.search(text, limit=7, type="track")
        links = list()
        number = 1
        for track in results["tracks"]["items"]:
            links.append(
                {"track_number": number,
                "link": track["external_urls"]["spotify"], 
                "song_name": track["name"],
                "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                "duration": strftime('%M:%S', gmtime(int(track["duration_ms"]) / 1000)),
                }
            )
            number += 1

        return links

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
        link = (
            f"https://open.spotify.com/{spotify_link_type}/{spotify_regex_match[0][-1]}"
        )

        return {"spotify_link_type": spotify_link_type, "link": link}


class File:
    def remove_file(self, path):
        remove(path)
        return True


class Deezer:
    def __init__(self):
        from deezer_downloader import deezer
        self.deezer = deezer

    def search_track(self, text):
        results = self.deezer.deezer_search(text)[:10]
        links = list()
        number = 1
        for track in results:
            links.append(
                {"track_number": number,
                "id": track["id"], 
                "song_name": track["title"],
                "artist": track["artist"],
                "duration": strftime('%M:%S', gmtime(int(track["duration"]))),
                }
            )
            number += 1

        return links

    def download_track(self, track_id):
        song = self.deezer.get_song_infos_from_deezer_website(track_id)
        music_path = self.deezer.download_song(song)["music_path"]
        cover_path = self.deezer.download_cover(song)["cover_path"]

        return {
            "cover_path": cover_path,
            "music_path": music_path,
            "error": None,
        }


    def search_and_download_track(self, results):
        song = results["name"]
        artist = results["artists"][0]["name"]
        artistfinder = results["artists"]
        fetures = ""
        if len(artistfinder) > 1:
            for lomi in range(0, len(artistfinder)):
                try:
                    if lomi < len(artistfinder) - 2:
                        artistft = artistfinder[lomi + 1]["name"] + " "
                        fetures += artistft
                    else:
                        artistft = artistfinder[lomi + 1]["name"] + " "
                        fetures += artistft
                except:
                    pass
        else:
            fetures = ""

        millis = results["duration_ms"]
        millis = int(millis)
        spotify_track_seconds = millis / 1000
        search_query = f"{song} {artist} {fetures}"
        search_query = " ".join(search_query.split())


        search_results = self.deezer.deezer_search(search_query)[:10]
        if search_results == list():
            return {"error": {"song_name": search_query}}

        for i in range(len(search_results)):
            if abs(int(spotify_track_seconds) - search_results[i]["duration"]) <= 1:
                track = search_results[i]
                break
            
        track_details = self.deezer.get_song_infos_from_deezer_website(track["id"])
        music_path = self.deezer.download_song(track_details)["music_path"]
        cover_path = self.deezer.download_cover(track_details)["cover_path"]


        return {
            "cover_path": cover_path,
            "music_path": music_path,
            "name": search_query,
            "error": None,
        }