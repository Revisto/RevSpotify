import re

def extract_spotify_id(url: str, type: str) -> str:
    pattern = rf"https?://(open\.)?spotify\.com/{type}/([a-zA-Z0-9]+)"
    match = re.search(pattern, url)
    return match.group(2) if match else None