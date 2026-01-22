def score_candidate(candidate: dict, artist: str) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    title = candidate["title"].lower()
    uploader = (candidate.get("uploader") or "").lower()
    duration = candidate.get("duration") or 0
    artist = artist.lower()

    # uploader signal
    if artist in uploader:
        score += 30
        reasons.append("uploader matches artist")

    # title signals
    if "official audio" in title:
        score += 40
        reasons.append("official audio")

    if "remaster" in title:
        score += 5
        reasons.append("remaster")

    if "lyrics" in title:
        score -= 30
        reasons.append("lyrics video")

    if "live" in title:
        score -= 40
        reasons.append("live version")

    if "full album" in title:
        score -= 100
        reasons.append("full album")

    # duration signals
    if 300 <= duration <= 500:
        score += 10
        reasons.append("expected song duration")

    if duration > 900:
        score -= 80
        reasons.append("suspiciously long duration")

    return score, reasons

def score_metadata(
    result: dict,
    expected_title: str,
    expected_artist: str,
    expected_duration: int,
) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    # title match
    if expected_title.lower() in result.get("trackName", "").lower():
        score += 40
        reasons.append("title match")

    # artist match
    if expected_artist.lower() in result.get("artistName", "").lower():
        score += 40
        reasons.append("artist match")

    # duration match
    actual = result.get("trackTimeMillis")
    if actual and abs(actual / 1000 - expected_duration) < 5:
        score += 20
        reasons.append("duration match")

    return score, reasons
