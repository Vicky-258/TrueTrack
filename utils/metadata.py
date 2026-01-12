import requests
from core.config import Config

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


def search_itunes(term: str, artist: str, limit: int = 5):
    params = {
        "term": f"{term} {artist}",
        "entity": "song",
        "limit": limit,
    }

    resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=Config.ITUNES_TIMEOUT)
    resp.raise_for_status()

    data = resp.json()
    return data.get("results", [])


