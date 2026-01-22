import os
from pathlib import Path

class Config:

    DEFAULT_LIBRARY_ROOT = Path.home() / "Music" / "library"

    LIBRARY_ROOT = Path(
        os.getenv("MUSIC_LIBRARY_ROOT", DEFAULT_LIBRARY_ROOT)
    ).expanduser()

    try:
        DB_PATH = Path(os.environ["TRUETRACK_DB_PATH"])
    except KeyError:
        raise RuntimeError(
            "TRUETRACK_DB_PATH is required but not set. "
            "Please configure it in your .env file."
        )

    ITUNES_MAX_RETRIES = 3
    ITUNES_TIMEOUT = 10
    ALBUM_ART_TIMEOUT = 10
    
