import requests

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


def search_itunes(term: str, artist: str, limit: int = 5):
    params = {
        "term": f"{term} {artist}",
        "entity": "song",
        "limit": limit,
    }

    resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    return data.get("results", [])

def score_metadata(candidate: dict, expected_title: str, expected_artist: str, duration: int):
    score = 0
    reasons = []

    title = candidate.get("trackName", "").lower()
    artist = candidate.get("artistName", "").lower()
    track_time = int(candidate.get("trackTimeMillis", 0) / 1000)

    if expected_title.lower() in title:
        score += 40
        reasons.append("title match")

    if expected_artist.lower() in artist:
        score += 40
        reasons.append("artist match")

    if abs(track_time - duration) <= 5:
        score += 20
        reasons.append("duration match")

    return score, reasons
