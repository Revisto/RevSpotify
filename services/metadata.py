import eyed3
import requests

def update_metadata(file_path, track_info):
    audiofile = eyed3.load(file_path)
    if audiofile.tag is None:
        audiofile.initTag()

    # Update text metadata
    audiofile.tag.title = track_info['track_name']
    audiofile.tag.artist = ', '.join(track_info['artist_names'])
    audiofile.tag.album = track_info.get('album_name', '')
    audiofile.tag.release_date = track_info.get('release_date', '')

    # Download cover photo
    cover_photo_url = track_info['cover_photo_url']
    response = requests.get(cover_photo_url)
    if response.status_code == 200:
        cover_data = response.content
        # Remove all existing images
        for image in audiofile.tag.images:
            audiofile.tag.images.remove(image.description)
        # Set new cover photo
        audiofile.tag.images.set(3, cover_data, 'image/jpeg', u'Cover')
    
    audiofile.tag.save()