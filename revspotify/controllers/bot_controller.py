import requests
from telegram import Update
from telegram.ext import ConversationHandler, CallbackContext
from validator_collection import is_numeric
from validator_collection.checkers import is_not_empty

from views.messages import View
from bot_models.bot_model import Deezer, Spotify, File, TelegramAssistant
from logger import Logger


def is_the_link_valid(func):
    def wrapper(*args, **kwargs):
        analyse_results = Spotify().analyse_spotify_link(args[0].update.message.text)
        if analyse_results is False:
            if args[0].update.message.chat.type == "private":
                args[0].update.message.reply_text(View.link_is_not_valid())
            return ConversationHandler.END
        return func(*args, **kwargs, analyse_results=analyse_results)

    return wrapper


def is_spotify_high_and_racist_again(func):
    def wrapper(*args, **kwargs):
        try:
            result = requests.get(
                "https://open.spotify.com/album/6rPU1BHqLneslZ1N1EvVdR", timeout=2
            )
            if result.status_code == 403:
                raise PermissionError("Spotify Is Racist")

        except PermissionError:
            args[0].update.message.reply_text(
                View.forbidden_spotify_or_spotify_is_high_and_racist_again()
            )
            return ConversationHandler.END
        return func(*args, **kwargs)

    return wrapper


class BotController:
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context

    @is_the_link_valid
    @is_spotify_high_and_racist_again
    def query(self, analyse_results):
        chat_id = self.update.message.chat.id
        Logger(self.context, self.update).log_info("query")

        link = analyse_results["link"]
        spotify_link_type = analyse_results["spotify_link_type"]

        wait_message = self.update.message.reply_text(View.wait())
        wait_message_id = wait_message.message_id

        if isinstance(self.context.user_data.get("wait_messages"), list) is False:
            self.context.user_data["wait_messages"] = list()
        self.context.user_data["wait_messages"].append(wait_message_id)

        spotify_links = list()
        if spotify_link_type == "track":
            spotify_links.append(link)

        elif spotify_link_type == "album":
            spotify_links = Spotify().album(link)
            if spotify_links is None:
                TelegramAssistant(self.context, self.update).delete_wait_messages(
                    chat_id
                )
                self.update.message.reply_text(View.not_found_link())
                return ConversationHandler.END

        elif spotify_link_type == "artist":
            artist_results = Spotify().top_tracks_artist(
                link, unique_name_suffix=f"{chat_id}{self.update.message.message_id}"
            )
            if (
                artist_results is None or
                artist_results["error"] == "No tracks in artist's top tracks"
            ):
                TelegramAssistant(self.context, self.update).delete_wait_messages(
                    chat_id
                )
                self.update.message.reply_text(View.not_found_link())
                if (
                    artist_results is not None and
                    artist_results.get("cover") is not None
                ):
                    File().remove_file(spotify_links["cover"])
                return ConversationHandler.END

            spotify_links = artist_results["spotify_links"]
            cover_path = artist_results.get("cover")

            caption = View.artist_caption(
                artist_results["name"], artist_results["genres"]
            )
            if cover_path is not None:
                self.update.message.reply_photo(open(cover_path, "rb"), caption=caption)
                File().remove_file(cover_path)
            else:
                self.update.message.reply_text(chat_id, caption=caption)

        elif spotify_link_type == "playlist":
            playlist_results = Spotify().playlist(
                link, unique_name_suffix=f"{chat_id}{self.update.message.message_id}"
            )
            if playlist_results is None:
                TelegramAssistant(self.context, self.update).delete_wait_messages(
                    chat_id
                )
                self.update.message.reply_text(View.not_found_link())
                return ConversationHandler.END

            spotify_links = playlist_results["spotify_links"]
            cover_path = playlist_results["cover"]

            if playlist_results["error"] == "No tracks in playlist":
                TelegramAssistant(self.context, self.update).delete_wait_messages(
                    chat_id
                )

                caption = View.playlist_is_empty()

                if cover_path is None:
                    self.update.message.reply_text(caption)

                else:
                    self.update.message.reply_photo(
                        open(cover_path, "rb"), caption=caption
                    )
                    File().remove_file(cover_path)

                return ConversationHandler.END

            caption = View.receive_count_of_playlist_songs_to_send(len(spotify_links))
            playlist_photo_with_caption_to_get_count_of_the_playlist = (
                self.update.message.reply_photo(open(cover_path, "rb"), caption=caption)
            )
            File().remove_file(cover_path)
            self.context.user_data["spotify_links"] = spotify_links
            self.context.user_data["playlist_photo_message"] = {
                "message_id": playlist_photo_with_caption_to_get_count_of_the_playlist.message_id,
                "name": playlist_results["name"],
            }
            return 1

        for spotify_link in spotify_links:
            track_download_result = Spotify().download_track(
                spotify_link,
                unique_name_suffix=f"{chat_id}{self.update.message.message_id}",
            )
            if track_download_result["error"] is not None:
                self.context.bot.delete_message(chat_id, wait_message_id)
                if track_download_result["error"] == "Invalid link":
                    self.update.message.reply_text(View.not_found_link())
                elif track_download_result["error"] == "Forbidden":
                    self.update.message.reply_text(
                        View.forbidden_spotify_or_spotify_is_high_and_racist_again()
                    )
                elif "song_name" in track_download_result["error"]:
                    self.update.message.reply_text(
                        View.error_downloading_track(
                            track_download_result["error"]["song_name"]
                        )
                    )
                else:
                    self.update.message.reply_text(View.unexpected_error())
                continue

            cover_path = track_download_result["cover_path"]
            if spotify_links.index(spotify_link) == 0 and spotify_link_type != "artist":
                self.update.message.reply_photo(open(cover_path, "rb"))
            File().remove_file(cover_path)

            music_path = track_download_result["music_path"]
            self.context.bot.send_audio(chat_id, open(music_path, "rb"))
            File().remove_file(music_path)

        TelegramAssistant(self.context, self.update).delete_wait_messages(chat_id)

        return ConversationHandler.END

    @is_spotify_high_and_racist_again
    def send_playlist(self):
        count = self.update.message.text
        chat_id = self.update.message.chat.id
        if "playlist_photo_message" in self.context.user_data:
            playlist_photo_message = self.context.user_data["playlist_photo_message"]
            self.context.bot.edit_message_caption(
                chat_id,
                playlist_photo_message["message_id"],
                caption=playlist_photo_message["name"],
            )
            self.context.user_data["playlist_photo_message"] = None

        if not is_numeric(count) or int(count) <= 0:
            self.update.message.reply_text(View.not_valid_number())
            TelegramAssistant(self.context, self.update).delete_wait_messages(chat_id)
            return ConversationHandler.END

        chosen_spotify_links = (self.context.user_data["spotify_links"])[: int(count)]

        for spotify_link in chosen_spotify_links:
            track_download_result = Spotify().download_track(
                spotify_link,
                unique_name_suffix=f"{chat_id}{self.update.message.message_id}",
            )
            if track_download_result["error"] is not None:
                if track_download_result["error"] == "Invalid link":
                    self.update.message.reply_text(View.not_found_link())
                elif track_download_result["error"] == "Forbidden":
                    self.update.message.reply_text(
                        View.forbidden_spotify_or_spotify_is_high_and_racist_again()
                    )
                elif "song_name" in track_download_result["error"]:
                    self.update.message.reply_text(
                        View.error_downloading_track(
                            track_download_result["error"]["song_name"]
                        )
                    )
                else:
                    self.update.message.reply_text(View.unexpected_error())
                continue

            File().remove_file(track_download_result["cover_path"])
            music_path = track_download_result["music_path"]
            self.context.bot.send_audio(chat_id, open(music_path, "rb"))
            File().remove_file(music_path)

        TelegramAssistant(self.context, self.update).delete_wait_messages(chat_id)

        self.update.message.reply_text(View.playlist_done())

        return ConversationHandler.END

    def start(self):
        Logger(self.context, self.update).log_info("start")
        welcome_message = View.welcome()
        self.update.message.reply_text(welcome_message)
        return True

    def cancel(self):
        Logger(self.context, self.update).log_info("cancel")
        if isinstance(self.context.user_data.get("wait_messages"), list):
            TelegramAssistant(self.context, self.update).delete_wait_messages(
                self.update.message.chat_id
            )

        self.update.message.reply_text(View.cancel())
        return ConversationHandler.END

    def search_intro(self):
        self.update.message.reply_text(View.search_intro())
        return 1

    def search_track(self):
        Logger(self.context, self.update).log_info("search_track")
        tracks = Deezer().search_track(self.update.message.text)

        if not is_not_empty(tracks):
            self.update.message.reply_text(View.no_results())
            return ConversationHandler.END

        self.update.message.reply_text(View.choose_from_search_results(tracks))
        self.context.user_data["search_tracks"] = tracks
        return 2

    def choose_from_search_results(self):
        if "search_tracks" not in self.context.user_data:
            self.update.message.reply_text(View.unexpected_error())
            return ConversationHandler.END

        tracks = self.context.user_data["search_tracks"]
        self.context.user_data.pop("search_tracks")
        order = self.update.message.text
        if not is_numeric(order) or int(order) <= 0 or int(order) > len(tracks):
            self.update.message.reply_text(View.not_valid_number())
            return ConversationHandler.END

        chat_id = self.update.message.chat.id
        wait_message = self.update.message.reply_text(View.wait())
        wait_message_id = wait_message.message_id
        track_download_result = Deezer().download_track(
            (tracks[int(self.update.message.text) - 1])["id"],
            unique_name_suffix=f"{chat_id}{self.update.message.message_id}",
        )
        if track_download_result["error"] is not None:
            self.context.bot.delete_message(chat_id, wait_message_id)
            if track_download_result["error"] == "Track not found":
                self.update.message.reply_text(View.error_downloading_track())
            return ConversationHandler.END

        cover_path = track_download_result["cover_path"]
        music_path = track_download_result["music_path"]
        self.context.bot.delete_message(chat_id, wait_message_id)
        self.update.message.reply_photo(open(cover_path, "rb"))
        File().remove_file(cover_path)
        self.context.bot.send_audio(chat_id, open(music_path, "rb"))
        File().remove_file(music_path)
        return ConversationHandler.END
