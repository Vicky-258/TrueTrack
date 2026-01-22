import os
from pathlib import Path

class Config:

    DEFAULT_LIBRARY_ROOT = Path.home() / "Music" / "library"

    LIBRARY_ROOT = Path(
        os.getenv("MUSIC_LIBRARY_ROOT", DEFAULT_LIBRARY_ROOT)
    ).expanduser()

    ITUNES_MAX_RETRIES = 3
    ITUNES_TIMEOUT = 10
    ALBUM_ART_TIMEOUT = 10
    
