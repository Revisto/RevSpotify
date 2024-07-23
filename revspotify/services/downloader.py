from services.deezer import DeezerService
from services.response import Response
from services.metadata import update_metadata
from logger import Logger

# from services.soundcloud import download_from_soundcloud
# from services.youtube import download_from_youtube

logger = Logger("downloader")

def download_track(track_info: dict):
    logger.info(f"Starting download for track: {track_info['track_name']} by {', '.join(track_info['artist_names'])}")
    deezer_service = DeezerService()
    deezer_query = f"{track_info['track_name']} {' '.join(track_info['artist_names'])}"
    logger.debug(f"Deezer query: {deezer_query}")
    track_response = deezer_service.search_and_download_track(
        query=deezer_query, duration_in_seconds=track_info["duration_ms"] // 1000
    )
    if track_response.is_success():
        file_path = track_response.music_address
        logger.info(f"Track downloaded successfully: {file_path}")
        update_metadata(file_path, track_info)
        logger.debug(f"Metadata updated for: {file_path}")
        return track_response

    logger.warning("Track download failed from Deezer, attempting other sources.")

    # download from soundcloud
    # logger.info("Attempting download from SoundCloud")
    # download_from_soundcloud(track_info)

    # download from youtube
    # logger.info("Attempting download from YouTube")
    # download_from_youtube(track_info)

    logger.warning(f"No matching track found in any service. for track: {track_info['track_name']} by {', '.join(track_info['artist_names'])}")
    return Response(error="No matching track found.", service="all")