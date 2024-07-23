from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers import (
    start,
    download_spotify_track,
    download_spotify_playlist,
    download_spotify_album,
)
from config.config import Config


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/track/([a-zA-Z0-9]+)"),
            download_spotify_track,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/album/([a-zA-Z0-9]+)"),
            download_spotify_album,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/playlist/([a-zA-Z0-9]+)"),
            download_spotify_playlist,
        )
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
