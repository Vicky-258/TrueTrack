import re


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def token_overlap(a: str, b: str) -> float:
    a_tokens = set(normalize(a).split())
    b_tokens = set(normalize(b).split())

    if not a_tokens or not b_tokens:
        return 0.0

    intersection = a_tokens & b_tokens
    return len(intersection) / max(len(a_tokens), len(b_tokens))


def score_metadata(
    result: dict,
    expected_title: str,
    expected_artist: str,
    expected_duration: int,
) -> tuple[int, list[str]]:

    score = 0
    reasons = []

    track_name = result.get("trackName", "")
    artist_name = result.get("artistName", "")
    actual_ms = result.get("trackTimeMillis")

    if not track_name or not artist_name or not actual_ms:
        return -1, ["missing critical metadata"]

    track_name_n = normalize(track_name)
    artist_name_n = normalize(artist_name)
    expected_title_n = normalize(expected_title)
    expected_artist_n = normalize(expected_artist)

    # -------------------------
    # HARD GATE: Duration
    # -------------------------
    delta = abs((actual_ms / 1000) - expected_duration)

    if delta > 7:
        return -1, [f"duration mismatch ({delta:.1f}s)"]

    score += 30
    reasons.append("duration within 7s")

    # -------------------------
    # Title similarity (token-based)
    # -------------------------
    title_sim = token_overlap(expected_title_n, track_name_n)

    if title_sim < 0.6:
        return -1, [f"weak title similarity ({title_sim:.2f})"]

    score += int(title_sim * 40)
    reasons.append(f"title similarity {title_sim:.2f}")

    # -------------------------
    # Artist similarity
    # -------------------------
    artist_sim = token_overlap(expected_artist_n, artist_name_n)

    if artist_sim < 0.5:
        return -1, [f"weak artist similarity ({artist_sim:.2f})"]

    score += int(artist_sim * 30)
    reasons.append(f"artist similarity {artist_sim:.2f}")

    # -------------------------
    # Penalize dangerous variants
    # -------------------------
    lowered = track_name_n

    if "live" in lowered:
        score -= 40
        reasons.append("live version penalty")

    if "remix" in lowered:
        score -= 40
        reasons.append("remix penalty")

    if "karaoke" in lowered:
        score -= 60
        reasons.append("karaoke penalty")

    if "instrumental" in lowered:
        score -= 30
        reasons.append("instrumental penalty")

    return score, reasons