from random import choice

class View:
    @staticmethod
    def welcome():
        message = (
            "سلام, من ربات RevsPotify هستم که میشه ترکیب @revisto و spotify!"
            "\nکاری که میکنم اینه که یه لینک اسپاتیفای از پلی‌لیست/ترک/آلبوم/آرتیست موردنظرتون میفرستید و من فایلشو براتون میفرستم."
            "\nهمه چی خیلی سادست, فقط یه لینک بفرستید."
            "\nخوش بگذرون و یادت نره من یه پروژه اوپن‌سورسم و آماده مشارکت شما :)"
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
        adverbs = ["اوکی!", "حله!", "عالی!", "صبر کن!"]
        adverb = choice(adverbs)
        message = f"{adverb} الان میفرستم."
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