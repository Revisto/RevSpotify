from telegram import Update, InputFile
from telegram.ext import ContextTypes
from io import BytesIO
import requests
import os

from bot.communications.message_handler import MessageHandler
from bot.utils import extract_spotify_id
from services.downloaders.spotify import SpotifyService
from services.downloaders.downloader import download_track
from logger import Logger


logger = Logger("handlers")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Received /start command from {update.effective_user.username}")
    await update.message.reply_text(MessageHandler().get_message("welcome_message"))


async def handle_track(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    track_info: dict,
) -> None:
    logger.info(
        f"Downloading track: {track_info['name']} by {track_info['artists'][0]['name']}"
    )

    track_info_summery = {
        "track_name": track_info["name"],
        "artist_names": [artist["name"] for artist in track_info["artists"]],
        "duration_ms": track_info["duration_ms"],
        "album_name": track_info["album"]["name"],
        "release_date": track_info["album"]["release_date"],
        "cover_photo_url": track_info["album"]["images"][0]["url"],
    }
    # print all album cover
    for image in track_info["album"]["images"]:
        print(image["url"])
    logger.info("Downloading track...")
    track_response = download_track(track_info_summery)
    if track_response.is_success():
        logger.info("Fetching track thumbnail")
        thumbnail_url = track_info["album"]["images"][0]["url"]
        response = requests.get(thumbnail_url)
        image = BytesIO(response.content)
        
        logger.info("Sending audio file")
        await update.message.reply_audio(audio=track_response.music_address, thumbnail=InputFile(image, filename="thumbnail.jpg"))
        
        logger.info("Deleting audio file")
        os.remove(track_response.music_address)
    else:
        logger.error(f"Error downloading track: {track_response.error}")
        await update.message.reply_text(track_response.error)


async def download_spotify_track(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.info(
        f"Received Spotify track link: {update.message.text} from {update.effective_user.username}"
    )
    track_id = extract_spotify_id(update.message.text, "track")
    track_info = SpotifyService().get_track_info(track_id)
    # send track cover once
    logger.info("Sending track cover photo")
    cover_photo_url = track_info["album"]["images"][0]["url"]
    caption = MessageHandler().get_message(
        "track_caption",
        track_name=track_info["name"],
        artist_name=", ".join([artist["name"] for artist in track_info["artists"]]),
        album_name=track_info["album"]["name"],
        release_date=track_info["album"]["release_date"],
    )
    await update.message.reply_photo(photo=cover_photo_url, caption=caption)
    waiting_message = await update.message.reply_text(
        MessageHandler().get_message("downloading_track", track_name=track_info["name"])
    )
    await handle_track(update, context, track_info)
    await waiting_message.delete()
    await update.message.reply_text(MessageHandler().get_message("task_done"))
    logger.info("Track download completed")


async def download_spotify_playlist(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.info(
        f"Received Spotify playlist link: {update.message.text} from {update.effective_user.username}"
    )
    playlist_id = extract_spotify_id(update.message.text, "playlist")
    playlist_info = SpotifyService().get_playlist_info(playlist_id)
    # send playlist cover once
    logger.info("Sending playlist cover photo")
    cover_photo_url = playlist_info["images"][0]["url"]
    caption = MessageHandler().get_message(
        "playlist_caption",
        playlist_name=playlist_info["name"],
        owner_name=playlist_info["owner"]["display_name"],
        total_tracks=playlist_info["tracks"]["total"],
    )
    await update.message.reply_photo(photo=cover_photo_url, caption=caption)
    for track in playlist_info["tracks"]["items"]:
        if track["track"]["is_local"] or track["track"]["track"] is not True:
            logger.info("Skipping local track")
            continue
        track_info = SpotifyService().get_track_info(track["track"]["id"])
        waiting_message = await update.message.reply_text(
            MessageHandler().get_message(
                "downloading_track", track_name=track_info["name"]
            )
        )
        await handle_track(update, context, track_info)
        await waiting_message.delete()

    await update.message.reply_text(MessageHandler().get_message("task_done"))
    logger.info("Playlist download completed")


async def download_spotify_album(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.info(
        f"Received Spotify album link: {update.message.text} from {update.effective_user.username}"
    )
    album_id = extract_spotify_id(update.message.text, "album")
    album_info = SpotifyService().get_album_info(album_id)
    # Send album cover once
    logger.info("Sending album cover photo")
    cover_photo_url = album_info["images"][0]["url"]
    caption = MessageHandler().get_message(
        "album_caption",
        album_name=album_info["name"],
        artist_name=", ".join([artist["name"] for artist in track_info["artists"]]),
        release_date=album_info["release_date"],
    )
    await update.message.reply_photo(photo=cover_photo_url, caption=caption)
    for track in album_info["tracks"]["items"]:
        track_info = SpotifyService().get_track_info(track["id"])
        waiting_message = await update.message.reply_text(
            MessageHandler().get_message(
                "downloading_track", track_name=track_info["name"]
            )
        )
        await handle_track(update, context, track_info)
        await waiting_message.delete()
    await update.message.reply_text(MessageHandler().get_message("task_done"))
    logger.info("Album download completed")


async def download_spotify_artist(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.info(
        f"Received Spotify artist link: {update.message.text} from {update.effective_user.username}"
    )
    artist_id = extract_spotify_id(update.message.text, "artist")
    artist_info = SpotifyService().get_artist_info(artist_id)
    # Send artist cover once
    logger.info("Sending artist cover photo")
    cover_photo_url = artist_info["images"][0]["url"]
    followers = artist_info["followers"]["total"]
    followers = "{:,}".format(followers)
    caption = MessageHandler().get_message(
        "artist_caption",
        artist_name=artist_info["name"],
        followers=followers,
        genres=", ".join(artist_info["genres"][:3]),
    )
    await update.message.reply_photo(photo=cover_photo_url, caption=caption)
    for track in artist_info["top_tracks"]:
        track_info = SpotifyService().get_track_info(track["id"])
        waiting_message = await update.message.reply_text(
            MessageHandler().get_message(
                "downloading_track", track_name=track_info["name"]
            )
        )
        await handle_track(update, context, track_info)
        await waiting_message.delete()
    await update.message.reply_text(MessageHandler().get_message("task_done"))
    logger.info("Artist download completed")
