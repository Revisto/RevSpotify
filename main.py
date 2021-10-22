from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
)

from handlers.handler import *
from config import Config

def main() -> None:
    updater = Updater(Config.token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler(["start", "help"], start_and_help))
    dispatcher.add_handler(CommandHandler(["track", "playlist", "artist", "album", "spotify", "download"], query))
    dispatcher.add_handler(MessageHandler(Filters.text, query))


    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
