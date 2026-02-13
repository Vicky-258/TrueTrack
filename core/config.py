import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file into environment
load_dotenv()

class Config:

    ENV_MUSIC_LIBRARY_ROOT = os.getenv("MUSIC_LIBRARY_ROOT")

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