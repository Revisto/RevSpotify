from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

from handlers.handler import (
    start_and_help,
    cancel,
    query,
    send_playlist,
    search_intro,
    search_track,
    choose_from_search_results,
)
from config import Config

PLAYLIST_COUNT = 1
GET_SONG_NAME_TO_SEARCH = 1
GET_MESSAGE_DATA_FROM_ADMIN = 1
CHOOSE_FROM_SEARCH_RESULTS = 2


def main() -> None:
    updater = Updater(Config.TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler(["start", "help"], start_and_help))

    playlist_converstation = ConversationHandler(
        entry_points=[MessageHandler(Filters.text, query)],
        states={
            PLAYLIST_COUNT: [
                CommandHandler(["cancel", "stop"], cancel),
                MessageHandler(Filters.text, send_playlist),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    search_converstation = ConversationHandler(
        entry_points=[CommandHandler(["search"], search_intro)],
        states={
            GET_SONG_NAME_TO_SEARCH: [
                CommandHandler(["cancel", "stop"], cancel),
                MessageHandler(Filters.text, search_track),
            ],
            CHOOSE_FROM_SEARCH_RESULTS: [
                CommandHandler(["cancel", "stop"], cancel),
                MessageHandler(Filters.text, choose_from_search_results),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(search_converstation)
    dispatcher.add_handler(playlist_converstation)

    updater.start_polling()
    updater.idle()

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
