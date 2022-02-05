import requests
from telegram.ext import ConversationHandler
from validator_collection import is_numeric
from validator_collection.checkers import is_not_empty

from views.messages import View
from bot_models.bot_model import Deezer, Spotify, File
from logger import Logger

# sample decorator


def is_the_link_valid(func):
    def wrapper(*args, **kwargs):
        analyse_results = Spotify().analyse_spotify_link(args[0].update.message.text)
        if analyse_results is False:
            if args[0].update.message["chat"]["type"] == "private":
                args[0].update.message.reply_text(View.link_is_not_valid())
            return ConversationHandler.END
        return func(*args, **kwargs, analyse_results=analyse_results)
    return wrapper

def is_spotify_high_and_racist_again(func):
    def wrapper(*args, **kwargs):
        try:
            result = requests.get("https://open.spotify.com", timeout=1)
            if result.status_code != 200:
                args[0].update.message.reply_text(View.forbidden_spotify_or_spotify_is_high_and_racist_again())
                return ConversationHandler.END
        except:
            args[0].update.message.reply_text(View.forbidden_spotify_or_spotify_is_high_and_racist_again())
            return ConversationHandler.END
        return func(*args, **kwargs)
    return wrapper

class BotController:
    def __init__(self, update, context):
        self.update = update
        self.context = context

    @is_the_link_valid
    @is_spotify_high_and_racist_again
    def query(self, analyse_results):
        chat_id = self.update.message["chat"]["id"]
        
        Logger(self.context, self.update).log_info("query")
        
        link = analyse_results["link"]
        spotify_link_type = analyse_results["spotify_link_type"]
        
        wait_message = self.update.message.reply_text(View().wait())
        wait_message_id = wait_message["message_id"]
        
        if isinstance(self.context.user_data.get("wait_messages"), list) is False:
            self.context.user_data["wait_messages"] = list()
        self.context.user_data["wait_messages"].append(wait_message_id)


        spotify_links = list()
        if spotify_link_type == "track":
            spotify_links.append(link)
        elif spotify_link_type == "album":
            spotify_links = Spotify().album(link)
        elif spotify_link_type == "artist":
            spotify_links = Spotify().top_tracks_artist(link)
        elif spotify_link_type == "playlist":
            spotify_links = Spotify().playlist(link)
            get_count_message = self.update.message.reply_text(View.receive_count_of_playlist_songs_to_send(len(spotify_links)))
            self.context.user_data["spotify_links"] = spotify_links
            self.context.user_data["wait_messages"].append(get_count_message["message_id"])
            return 1

        for spotify_link in spotify_links:
            track_download_result = Spotify().download_track(spotify_link)

            if track_download_result["error"] is not None:
                self.context.bot.delete_message(chat_id, wait_message_id)
                self.update.message.reply_text(View.error_downloading_track(track_download_result["error"]["song_name"]))
                continue

            if spotify_link_type == "track":
                cover_path = track_download_result["cover_path"]
                self.update.message.reply_photo(open(cover_path, "rb"))
            File().remove_file(cover_path)

            music_path = track_download_result["music_path"]
            self.update.message.reply_audio(open(music_path, "rb"))
            File().remove_file(music_path)
        
        for message_id in self.context.user_data.get("wait_messages"):
            self.context.bot.delete_message(self.update.message["chat"]["id"], message_id)
            self.context.user_data.get("wait_messages").remove(message_id)
        return ConversationHandler.END


    def send_playlist(self):
        count = self.update.message.text
        chat_id = self.update.message["chat"]["id"]
        if not is_numeric(count) or int(count) <= 0:
            for message_id in self.context.user_data.get("wait_messages"):
                self.context.bot.delete_message(chat_id, message_id)
                self.context.user_data["wait_messages"].remove(message_id)
            return ConversationHandler.END            

        chosen_spotify_links = (self.context.user_data["spotify_links"])[:int(count)]
        
        for spotify_link in chosen_spotify_links:
            track_download_result = Spotify().download_track(spotify_link)
            
            if track_download_result["error"] is not None:
                self.update.message.reply_text(View.error_downloading_track(track_download_result["error"]["song_name"]))
                continue

            File().remove_file(track_download_result["cover_path"])
            music_path = track_download_result["music_path"]
            self.context.bot.send_audio(chat_id, open(music_path, "rb"))
            File().remove_file(music_path)
        
        for message_id in self.context.user_data.get("wait_messages"):
            self.context.bot.delete_message(chat_id, message_id)
            self.context.user_data["wait_messages"].remove(message_id)

        self.update.message.reply_text(View.playlist_done())
        return ConversationHandler.END


    def start(self):
        Logger(self.context, self.update).log_info("start")
        welcome_message = View.welcome()
        self.update.message.reply_text(welcome_message)
        return True

    def cancel(self):
        Logger(self.context, self.update).log_info("cancel")
        for message_id in self.context.user_data.get("wait_messages"):
            self.context.bot.delete_message(self.update.message["chat"]["id"], message_id)
            self.context.user_data["wait_messages"].remove(message_id)

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
        track_download_result = Deezer().download_track((tracks[int(self.update.message.text) - 1])["id"])
        if track_download_result["error"] is not None:
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_text(View.error_downloading_track(track_download_result["error"]["song_name"]))
            return ConversationHandler.END

        cover_path = track_download_result["cover_path"]
        music_path = track_download_result["music_path"]
        self.context.bot.delete_message(chat_id, wait_message_id)
        self.update.message.reply_photo(open(cover_path, "rb"))
        File().remove_file(cover_path)
        self.context.bot.send_audio(chat_id, open(music_path, "rb"))
        File().remove_file(music_path)
        return ConversationHandler.END

    def send_message_from_admin_intro_and_auth(self):
        if self.update.message.from_user["username"].lower() != "revisto":
            self.update.message.reply_text(View.not_admin())
            return ConversationHandler.END
        self.update.message.reply_text(View.send_message_from_admin_intro())
        return 1
    
    def send_message_from_admin_data(self):
        text = self.update.message.text
        splitted_text = text.split("\n")
        if len(splitted_text) == 2:
            splitted_text.append("")
        try:
            if len(splitted_text) < 3:
                raise Exception()
            chat_id = splitted_text[0]
            message = "\n".join(splitted_text[1:-1])
            reply_to_message_id = splitted_text[-1]
            self.context.bot.send_message(chat_id, message, reply_to_message_id=reply_to_message_id)
            self.update.message.reply_text(View.sent_message_from_admin())
        except:
            self.update.message.reply_text(View.error_sending_message_from_admin())
        return ConversationHandler.END