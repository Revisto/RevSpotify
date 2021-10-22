from views.messages import View
from bot_models.bot_model import Spotify, File

class BotController:
    def __init__(self, update, context):
        self.update = update
        self.context = context

    def query(self):
        link = self.update.message.text
        chat_id = self.update.message["chat"]["id"]
        analyse_results = Spotify().analyse_spotify_link(link)
        print(analyse_results)
        if analyse_results is False:
            self.update.message.reply_text(View.link_is_not_valid())
            return
        link = analyse_results["link"]
        spotify_link_type = analyse_results["spotify_link_type"]
        wait_message = self.update.message.reply_text(View().wait())
        wait_message_id = wait_message["message_id"]

        if spotify_link_type == "track":
            track_download_result = Spotify().download_track(link)
            if track_download_result["error"] is not None:
                self.context.bot.delete_message(chat_id, wait_message_id)
                self.update.message.reply_text(track_download_result["error"])
                return

            cover_path = track_download_result["cover_path"]
            music_path = track_download_result["music_path"]
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_photo(open(cover_path, "rb"))
            File().remove_file(cover_path)
            self.context.bot.send_audio(chat_id, open(music_path, "rb"))
            File().remove_file(music_path)

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
            return

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
            return

        if spotify_link_type == "playlist":
            playlist_tracks_links = Spotify().playlist(link)
            for playlist_tracks_link in playlist_tracks_links:
                track_download_result = Spotify().download_track(playlist_tracks_link)
                if track_download_result["error"] is not None:
                    self.update.message.reply_text(track_download_result["error"])
                    continue

                File().remove_file(track_download_result["cover_path"])
                music_path = track_download_result["music_path"]
                self.context.bot.send_audio(chat_id, open(music_path, "rb"))
                File().remove_file(music_path)
            self.context.bot.delete_message(chat_id, wait_message_id)
            self.update.message.reply_text(View.playlist_done())
            return

    def start(self):
        welcome_message = View.welcome()
        self.update.message.reply_text(welcome_message)
        return True
