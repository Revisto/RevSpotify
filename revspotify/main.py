from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers import (
    start,
    download_spotify_track,
    download_spotify_playlist,
    download_spotify_album,
    download_spotify_artist,
)
from config.config import Config

# Import the Logger class
from logger import Logger


def main() -> None:
    """Start the bot."""
    # Instantiate the Logger
    logger = Logger("RevSpotify")

    logger.info("Starting the bot")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    logger.info("Added handler for /start command")

    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/track/([a-zA-Z0-9]+)"),
            download_spotify_track,
        )
    )
    logger.info("Added handler for Spotify track links")

    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/album/([a-zA-Z0-9]+)"),
            download_spotify_album,
        )
    )
    logger.info("Added handler for Spotify album links")

    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/playlist/([a-zA-Z0-9]+)"),
            download_spotify_playlist,
        )
    )
    logger.info("Added handler for Spotify playlist links")

    application.add_handler(
        MessageHandler(
            filters.Regex(r"https?://(open\.)?spotify\.com/artist/([a-zA-Z0-9]+)"),
            download_spotify_artist,
        )
    )
    logger.info("Added handler for Spotify artist links")

    # Run the bot until the user presses Ctrl-C
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Bot stopped")


if __name__ == "__main__":
    main()
