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
