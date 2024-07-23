from services.deezer import DeezerService
from services.response import Response
from services.metadata import update_metadata

# from services.soundcloud import download_from_soundcloud
# from services.youtube import download_from_youtube


def download_track(track_info: dict):
    # download from deezer
    deezer_service = DeezerService()
    deezer_query = f"{track_info['track_name']} {' '.join(track_info['artist_names'])}"
    track_response = deezer_service.search_and_download_track(
        query=deezer_query, duration_in_seconds=track_info["duration_ms"] // 1000
    )
    if track_response.is_success():
        file_path = track_response.music_address
        update_metadata(file_path, track_info)
        return track_response

    # download from soundcloud
    # download_from_soundcloud(track_info)

    # download from youtube
    # download_from_youtube(track_info)

    return Response(error="No matching track found.", service="all")
