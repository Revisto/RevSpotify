from deezer_downloader.deezer import Deezer404Exception
from spotify_downloader.exceptions import SpotifyException
import spotify_downloader
from spotify_downloader.oauth2 import SpotifyClientCredentials
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

        self.spotify = spotify_downloader.Spotify(
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

    def humanize_youtube_results(self, results):
        for result in results:
            result["duration"] = self.convert_youtube_time_duration_to_seconds(
                result["duration"]
            )
            result["views"] = int(result["views"].replace(",", "").replace(" views", "").replace(" view", ""))
        return results


    def download_track(self, link, unique_name_suffix):
        try:
            results = self.spotify.track(link)
        except AttributeError:
            return {"error": "Forbidden"}
        except SpotifyException:
            return {"error": "Invalid link"}
        deezer_results = Deezer().search_and_download_track(results, unique_name_suffix)
        if deezer_results["error"] is None:
            return deezer_results

        youtube_results = self.download_track_from_youtube(results, unique_name_suffix)
        return youtube_results

    def download_track_from_youtube(self, results, unique_name_suffix=None):
        song = results["name"]
        artist = results["artists"][0]["name"]
        search_query = str(song + " " + artist)
        artistfinder = results["artists"]
        album = results["album"]["name"]
        realese_date = int(results["album"]["release_date"][:4])

        if len(artistfinder) > 1:
            fetures = " (Ft."
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
        trackname = trackname.replace("/", "-").replace("\\", "-")
        if unique_name_suffix is not None:
            cover_path = f"static/covers/{trackname}-{unique_name_suffix}.png"
            music_path = f"static/songs/{trackname}-{unique_name_suffix}.mp3"
        else:
            cover_path = f"static/covers/{trackname}.png"
            music_path = f"static/songs/{trackname}.mp3"

        # search for music on youtube
        yt_results = self.humanize_youtube_results(list(YoutubeSearch(str(search_query)).to_dict()))
        best_result = {"duration": float("inf"), "views": -1, "found": False}
        for yt_result in yt_results:
            if yt_results.index(yt_result) > 4 and best_result.get("found") is not False:
                break
            this_duration_diff = abs(yt_result["duration"] - spotify_track_seconds)
            if this_duration_diff <= 4:
                duration_diff_with_the_best = abs(best_result["duration"] - spotify_track_seconds)
                if (this_duration_diff < duration_diff_with_the_best) or (this_duration_diff == duration_diff_with_the_best and yt_result["views"] > best_result["views"]):
                    best_result = yt_result

        print(search_query, best_result)
        if best_result.get("found") is False:
            return {"error": {"song_name": song}}

        requests.get("http://test.revs.ir/{}".format(best_result["url_suffix"]))

        chosen_youtube_link = str("https://www.youtube.com/" + best_result["url_suffix"])
        options = {
            # PERMANENT options
            "format": "bestaudio/best",
            "keepvideo": False,
            "outtmpl": music_path,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }

        # Download Cover
        response = requests.get(results["album"]["images"][0]["url"])
        file = open(cover_path, "wb")
        file.write(response.content)
        file.close()

        with yt_dlp.YoutubeDL(options) as mp3:
            mp3.download([chosen_youtube_link])

        aud = eyed3.load(music_path)
        aud.tag.artist = artist
        aud.tag.album = album
        aud.tag.album_artist = artist
        aud.tag.title = trackname
        aud.tag.year = realese_date
        aud.tag.images.set(3, open(cover_path, "rb").read(), "image/png")
        aud.tag.save()
        return {
            "cover_path": cover_path,
            "music_path": music_path,
            "name": trackname,
            "error": None,
        }

    def search_track(self, text):
        """Not working, need to fix"""

        results = self.spotify.search(text, limit=7, type="track")
        links = list()
        number = 1
        for track in results["tracks"]["items"]:
            links.append(
                {
                    "track_number": number,
                    "link": track["external_urls"]["spotify"],
                    "song_name": track["name"],
                    "artist": ", ".join(
                        [artist["name"] for artist in track["artists"]]
                    ),
                    "duration": strftime(
                        "%M:%S", gmtime(int(track["duration_ms"]) / 1000)
                    ),
                }
            )
            number += 1

        return links

    def album(self, link):
        try:
            results = self.spotify.album_tracks(link)
        except:
            return None

        tracks = list()
        for track in results["items"]:
            tracks.append(track["external_urls"]["spotify"])

        return tracks

    def top_tracks_artist(self, link, unique_name_suffix):
        try:
            results = self.spotify.artist_top_tracks(link)
        except:
            return None

        top_tracks = list()
        for top_track in results["tracks"]:
            top_tracks.append(top_track["external_urls"]["spotify"])
        if results["artist"]["images"] == []:
            cover_path = None
        else:
            cover_path = (
                f"static/covers/{results['artist']['name']}-{unique_name_suffix}.png"
            )
            response = requests.get(results["artist"]["images"][0]["url"])
            file = open(cover_path, "wb")
            file.write(response.content)
            file.close()

        error = None
        if top_tracks == []:
            error = "No tracks in artist's top tracks"

        return {
            "spotify_links": top_tracks,
            "cover": cover_path,
            "name": results["artist"]["name"],
            "genres": results["artist"]["genres"],
            "error": error,
        }

    def playlist(self, link, unique_name_suffix):
        try:
            results = self.spotify.playlist_tracks(link)
        except:
            return None

        error = None
        playlist_tracks = list()
        for track in results["tracks"]["items"]:
            playlist_tracks.append(track["track"]["external_urls"]["spotify"])

        if results["images"] == []:
            cover_path = None
        else:
            cover_path = f"static/covers/{results['name']}-{unique_name_suffix}.png"
            response = requests.get(results["images"][0]["url"])
            file = open(cover_path, "wb")
            file.write(response.content)
            file.close()

        if playlist_tracks == []:
            error = "No tracks in playlist"

        return {
            "spotify_links": playlist_tracks,
            "cover": cover_path,
            "name": results["name"],
            "error": error,
        }

    def analyse_spotify_link(self, text):
        spotify_regex = r"(\/(track|playlist|artist|album|spotify|download)@revspotifybot )?(https?:\/\/)?(www\.)?(open.spotify)\.(com)\/(track|album|artist|playlist)\/([^ \n&\.=%\?]{20,23})"
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
                {
                    "track_number": number,
                    "id": track["id"],
                    "song_name": track["title"],
                    "artist": track["artist"],
                    "duration": strftime("%M:%S", gmtime(int(track["duration"]))),
                }
            )
            number += 1

        return links

    def download_track(self, track_id, unique_name_suffix):
        try:
            song = self.deezer.get_song_infos_from_deezer_website(track_id)
        except Deezer404Exception:
            return {"error": "Track not found"}
        music_path = self.deezer.download_song(
            song, unique_name_suffix=unique_name_suffix
        )["music_path"]
        cover_path = self.deezer.download_cover(
            song, unique_name_suffix=unique_name_suffix
        )["cover_path"]

        return {
            "cover_path": cover_path,
            "music_path": music_path,
            "error": None,
        }

    def search_and_download_track(self, results, unique_name_suffix):
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


        best_result = {"duration": float("inf"), "rank": float("inf"), "found": False}
        print("\n\n\n\n\n\n")
        print(search_results)
        print("\n\n\n\n\n\n")
        for deezer_result in search_results:
            if search_results.index(deezer_result) > 4 and best_result.get("found") is not False:
                break
            this_duration_diff = abs(spotify_track_seconds - deezer_result["duration"])
            if this_duration_diff <= 2:
                duration_diff_with_the_best = abs(best_result["duration"] - spotify_track_seconds)
                if (this_duration_diff < duration_diff_with_the_best) or (this_duration_diff == duration_diff_with_the_best and deezer_result["rank"] > best_result["rank"]):
                    best_result = deezer_result

        print(search_query, best_result)
        if best_result.get("found") is False:
            return {"error": {"song_name": search_query}}

        track_details = self.deezer.get_song_infos_from_deezer_website(best_result["id"])
        music_path = self.deezer.download_song(track_details, unique_name_suffix)[
            "music_path"
        ]
        cover_path = self.deezer.download_cover(track_details, unique_name_suffix)[
            "cover_path"
        ]

        return {
            "cover_path": cover_path,
            "music_path": music_path,
            "name": search_query,
            "error": None,
        }


class TelegramAssistant:
    def __init__(self, context, update):
        self.context = context
        self.update = update

    def delete_wait_messages(self, chat_id):
        for message_id in self.context.user_data.get("wait_messages")[:]:
            self.context.bot.delete_message(chat_id, message_id)
            self.context.user_data["wait_messages"].remove(message_id)
