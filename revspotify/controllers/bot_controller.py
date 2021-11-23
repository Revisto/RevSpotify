from telegram.ext import ConversationHandler
from validator_collection import is_numeric
from validator_collection.checkers import is_not_empty

from views.messages import View
from bot_models.bot_model import Spotify, File
from logger import Logger

class BotController:
    def __init__(self, update, context):
        self.update = update
        self.context = context

    def query(self):
        text = self.update.message.text
        chat_id = self.update.message["chat"]["id"]
        analyse_results = Spotify().analyse_spotify_link(text)
        if analyse_results is False:
            if self.update.message["chat"]["type"] == "private":
                self.update.message.reply_text(View.link_is_not_valid())
            return ConversationHandler.END
        Logger(self.context, self.update).log_info(self.update.message.from_user, "query", text)
        link = analyse_results["link"]
        spotify_link_type = analyse_results["spotify_link_type"]
        wait_message = self.update.message.reply_text(View().wait())
        wait_message_id = wait_message["message_id"]

        if spotify_link_type == "track":
            track_download_result = Spotify().download_track(link)
            if track_download_result["error"] is not None:
                self.context.bot.delete_message(chat_id, wait_message_id)
                self.update.message.reply_text(track_download_result["error"])
                return ConversationHandler.END

            cover_path = track_download_result["cover_path"]
            music_path = track_download_result["music_path"]
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_photo(open(cover_path, "rb"))
            File().remove_file(cover_path)
            self.context.bot.send_audio(chat_id, open(music_path, "rb"))
            File().remove_file(music_path)
            return ConversationHandler.END

        if spotify_link_type == "album":
            album_links = Spotify().album(link)
            for album_link in album_links:
                track_download_result = Spotify().download_track(album_link)
                if track_download_result["error"] is not None:
                    self.update.message.reply_text(track_download_result["error"])
                    continue

                File().remove_file(track_download_result["cover_path"])
                music_path = track_download_result["music_path"]
                self.context.bot.send_audio(chat_id, open(music_path, "rb"))
                File().remove_file(music_path)
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_text(View.album_done())
            return ConversationHandler.END

        if spotify_link_type == "artist":
            artist_top_tracks_links = Spotify().top_tracks_artist(link)
            for artist_top_tracks_link in artist_top_tracks_links:
                track_download_result = Spotify().download_track(artist_top_tracks_link)
                if track_download_result["error"] is not None:
                    self.update.message.reply_text(track_download_result["error"])
                    continue

                File().remove_file(track_download_result["cover_path"])
                music_path = track_download_result["music_path"]
                self.context.bot.send_audio(chat_id, open(music_path, "rb"))
                File().remove_file(music_path)
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_text(View.artist_done())
            return ConversationHandler.END

        if spotify_link_type == "playlist":
            playlist_tracks_links = Spotify().playlist(link)
            get_count_message = self.update.message.reply_text(View.receive_count_of_playlist_songs_to_send(len(playlist_tracks_links)))
            self.context.user_data["playlist_tracks_links"] = playlist_tracks_links
            self.context.user_data["chat_id"] = chat_id
            self.context.user_data["wait_message_id"] = wait_message_id
            self.context.user_data["second_wait_message_id"] = get_count_message["message_id"]
            return 1

    def send_playlist(self):
        count = self.update.message.text
        chat_id = self.context.user_data["chat_id"]
        first_wait_message_id = self.context.user_data["wait_message_id"]
        second_wait_message_id = self.context.user_data["second_wait_message_id"]
        if not is_numeric(count) or int(count) <= 0:
            self.context.bot.delete_message(chat_id, first_wait_message_id)
            self.context.bot.delete_message(chat_id, second_wait_message_id)
            self.update.message.reply_text(View.not_valid_number())
            return ConversationHandler.END

        playlist_tracks_links = (self.context.user_data["playlist_tracks_links"])[:int(count)]
        for playlist_tracks_link in playlist_tracks_links:
            track_download_result = Spotify().download_track(playlist_tracks_link)
            if track_download_result["error"] is not None:
                self.update.message.reply_text(track_download_result["error"])
                continue

            File().remove_file(track_download_result["cover_path"])
            music_path = track_download_result["music_path"]
            self.context.bot.send_audio(self.context.user_data["chat_id"], open(music_path, "rb"))
            File().remove_file(music_path)
        self.context.bot.delete_message(chat_id, first_wait_message_id)
        self.context.bot.delete_message(chat_id, second_wait_message_id)
        self.update.message.reply_text(View.playlist_done())
        return ConversationHandler.END

    def start(self):
        Logger(self.context, self.update).log_info(self.update.message.from_user, "start", self.update.message.text)
        welcome_message = View.welcome()
        self.update.message.reply_text(welcome_message)
        return True

    def cancel(self):
        Logger(self.context, self.update).log_info(self.update.message.from_user, "cancel", self.update.message.text)
        try:
            self.context.bot.delete_message(self.context.user_data["chat_id"], self.context.user_data["wait_message_id"])
        except:
            pass

        try:
            self.context.bot.delete_message(self.context.user_data["chat_id"], self.context.user_data["second_wait_message_id"])
        except:
            pass

        self.update.message.reply_text(View.cancel())
        return ConversationHandler.END

    def search_intro(self):
        self.update.message.reply_text(View.search_intro())
        return 1

    def search_track(self):
        Logger(self.context, self.update).log_info(self.update.message.from_user, "search_track", self.update.message.text)
        tracks = Spotify().search_track(self.update.message.text)
        if not is_not_empty(tracks):
            self.update.message.reply_text(View.no_results())
            return ConversationHandler.END

        self.update.message.reply_text(View.choose_from_search_results(tracks))
        self.context.user_data["search_tracks"] = tracks
        return 2

    def choose_from_search_results(self):
        if "search_tracks" not in self.context.user_data:
            self.update.message.reply_text(View.error())
            return ConversationHandler.END
        
        tracks = self.context.user_data["search_tracks"]
        self.context.user_data.pop("search_tracks")
        order = self.update.message.text
        if not is_numeric(order) or int(order) <= 0 or int(order) > len(tracks):
            self.update.message.reply_text(View.not_valid_number())
            return ConversationHandler.END

        chat_id = self.update.message["chat"]["id"]
        wait_message = self.update.message.reply_text(View().wait())
        wait_message_id = wait_message["message_id"]
        track_download_result = Spotify().download_track(tracks[int(self.update.message.text) - 1]["link"])
        if track_download_result["error"] is not None:
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_text(track_download_result["error"])
            return ConversationHandler.END

        cover_path = track_download_result["cover_path"]
        music_path = track_download_result["music_path"]
        self.context.bot.delete_message(chat_id, wait_message_id)
        self.update.message.reply_photo(open(cover_path, "rb"))
        File().remove_file(cover_path)
        self.context.bot.send_audio(chat_id, open(music_path, "rb"))
        File().remove_file(music_path)
        return ConversationHandler.END