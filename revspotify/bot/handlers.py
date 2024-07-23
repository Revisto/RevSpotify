from telegram import Update
from telegram.ext import ContextTypes
import os

from bot.communications.message_handler import MessageHandler
from bot.utils import extract_spotify_id
from services.spotify import SpotifyService
from services.downloader import download_track


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(MessageHandler().get_message("welcome_message"))


async def handle_track(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    track_info: dict,
    send_wait_message: bool = True,
    send_cover: bool = True,
) -> None:
    messages_to_delete = []

    if send_wait_message:
        proccessing_message = await update.message.reply_text(
            MessageHandler().get_message("processing_message")
        )
        messages_to_delete.append(proccessing_message.message_id)

    if send_cover:
        cover_photo_url = track_info["album"]["images"][0]["url"]
        caption = MessageHandler().get_message(
            "track_caption",
            track_name=track_info["name"],
            artist_name=track_info["artists"][0]["name"],
            album_name=track_info["album"]["name"],
            release_date=track_info["album"]["release_date"],
        )
        await update.message.reply_photo(photo=cover_photo_url, caption=caption)

    track_info_summery = {
        "track_name": track_info["name"],
        "artist_names": [artist["name"] for artist in track_info["artists"]],
        "duration_ms": track_info["duration_ms"],
        "album_name": track_info["album"]["name"],
        "release_date": track_info["album"]["release_date"],
        "cover_photo_url": track_info["album"]["images"][0]["url"],
    }

    track_response = download_track(track_info_summery)
    if track_response.is_success():
        await update.message.reply_audio(audio=track_response.music_address)
        os.remove(track_response.music_address)
    else:
        await update.message.reply_text(track_response.error)

    for message_id in messages_to_delete:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=message_id
        )


async def download_spotify_track(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    track_id = extract_spotify_id(update.message.text, "track")
    track_info = SpotifyService().get_track_info(track_id)
    await handle_track(update, context, track_info)


async def download_spotify_playlist(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    playlist_id = extract_spotify_id(update.message.text, "playlist")
    playlist_info = SpotifyService().get_playlist_info(playlist_id)
    # send playlist cover once
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
            continue
        track_info = SpotifyService().get_track_info(track["track"]["id"])
        await handle_track(
            update, context, track_info, send_wait_message=False, send_cover=False
        )


async def download_spotify_album(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    album_id = extract_spotify_id(update.message.text, "album")
    album_info = SpotifyService().get_album_info(album_id)
    # Send album cover once
    cover_photo_url = album_info["images"][0]["url"]
    caption = MessageHandler().get_message(
        "album_caption",
        album_name=album_info["name"],
        artist_name=album_info["artists"][0]["name"],
        release_date=album_info["release_date"],
    )
    await update.message.reply_photo(photo=cover_photo_url, caption=caption)
    for track in album_info["tracks"]["items"]:
        track_info = SpotifyService().get_track_info(track["id"])
        await handle_track(
            update, context, track_info, send_wait_message=False, send_cover=False
        )
