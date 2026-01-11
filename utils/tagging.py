import requests


def fetch_album_art(metadata: dict) -> bytes | None:
    """
    Fetch highest available album art.
    Prefer 100x100, but upscale URL to 600x600 if possible.
    """
    url = metadata.get("artworkUrl100")
    if not url:
        return None

    # iTunes trick: replace size with higher res
    hi_res = url.replace("100x100bb", "600x600bb")

    resp = requests.get(hi_res, timeout=10)
    resp.raise_for_status()

    return resp.content
