import eyed3
import requests
from logger import Logger

logger = Logger("metadata")

def update_metadata(file_path, track_info):
    logger.info(f"Updating metadata for {file_path}")
    audiofile = eyed3.load(file_path)
    if audiofile.tag is None:
        audiofile.initTag()
        logger.debug("Initialized new tag for audio file")

    # Update text metadata
    audiofile.tag.title = track_info["track_name"]
    audiofile.tag.artist = track_info["artist_names"][0]
    audiofile.tag.album = track_info.get("album_name", "")
    audiofile.tag.release_date = track_info.get("release_date", "")
    logger.info(f"Updated text metadata for {file_path}")

    # Download cover photo
    cover_photo_url = track_info["cover_photo_url"]
    response = requests.get(cover_photo_url)
    if response.status_code == 200:
        cover_data = response.content
        # Remove all existing images
        for image in audiofile.tag.images:
            audiofile.tag.images.remove(image.description)
        # Set new cover photo
        audiofile.tag.images.set(3, cover_data, "image/jpeg", "Cover")
        logger.info(f"Updated cover photo for {file_path}")
    else:
        logger.warning(f"Failed to download cover photo from {cover_photo_url}")

    audiofile.tag.save()
    logger.info(f"Successfully saved metadata for {file_path}")