from time import strftime
from telegram import message


class View:
    @staticmethod
    def welcome():
        message = (
            "سلام, من ربات RevSpotify هستم که میشه ترکیب @revisto و spotify!"
            "\nکاری که میکنم اینه که یه لینک اسپاتیفای از پلی‌لیست/ترک/آلبوم/آرتیست موردنظرتون میفرستید و من فایلشو براتون میفرستم."
            "\nهمه چی خیلی سادست, فقط یه لینک بفرستید."
            "\nراستی تو میتونی با کامند /search بین آهنگ‌ها هم سرچ کنی."
            "\nخوش بگذرون و یادت نره من یه پروژه اوپن‌سورسم و آماده مشارکت شما :)"
            "\nراستی, من یه سیستم لاگر دارم و آهنگ‌هایی که ازم میخوای بفرستم رو همراه با دیتای شما ذخیره میکنم."
            "\n"
            "\n"
            "\n"
            "\nhttps://github.com/Revisto/RevSpotify"
        )
        return message

    @staticmethod
    def link_is_not_valid():
        message = "این لینک اسپاتیفای نیست :("
        return message

    @staticmethod
    def wait():
        message = "صبر کن, الان میفرستم."
        return message

    @staticmethod
    def playlist_done():
        message = "اینم از موزیک‌های پلی لیست."
        return message

    @staticmethod
    def artist_done():
        message = "اینم از موزیک‌های برتر این آرتیست."
        return message

    @staticmethod
    def album_done():
        message = "اینم از موزیک‌های این آلبوم."
        return message

    @staticmethod
    def receive_count_of_playlist_songs_to_send(count):
        message = f"این پلی لیست {count}تا موزیک داره. چندتاشو بفرستم؟"
        return message

    @staticmethod
    def cancel():
        message = "کنسل گردید :)"
        return message
    
    @staticmethod
    def not_valid_number():
        message = "این عدد معتبر نیست :( \n پروسه کنسل شد."
        return message

    @staticmethod
    def search_intro():
        message = "دنبال چه آهنگی میگردی؟"
        return message

    @staticmethod
    def choose_from_search_results(tracks):
        message = "کدومشون؟ \n\n"
        for track in tracks:
            message += f"{track['track_number']} - {track['song_name']} from {track['artist']} - {track['duration']} \n\n"
        return message
    
    @staticmethod
    def no_results():
        message = "نتیجه ای پیدا نشد :("
        return message

    @staticmethod
    def error_downloading_track(song_name=None):
        if song_name is None:
            message = f"مشکلی در دانلود این آهنگ پیش اومده!"
        else:
            message = f"آهنگ {song_name} پیدا نشد!"
        return message

    @staticmethod
    def forbidden_spotify_or_spotify_is_high_and_racist_again():
        message = "خب, اسپاتیفای دوباره مست و نژادپرست شده و دسترسی ما رو بن کرده. به ادمین پیام بدید."
        return message

    @staticmethod
    def not_found_link():
        message = "لینک نامعتبر است :("
        return message

    @staticmethod
    def playlist_is_empty():
        message = "این پلی لیست خالی است :("
        return message

    @staticmethod
    def artist_caption(artist_name, genres: list):
        message = f"{artist_name}\n{' - '.join([genre.title() for genre in genres])}"
        return message

    @staticmethod
    def unexpected_error():
        message = "متاسفم، مشکلی پیش اومده. به ادمین پیام بدید."
        return message