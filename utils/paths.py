import tempfile
from pathlib import Path

BASE_TEMP_DIR = Path(tempfile.gettempdir()) / "music_ingest"


def ensure_job_temp_dir(job_id: str) -> Path:
    path = BASE_TEMP_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path
