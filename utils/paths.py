import os

BASE_TEMP_DIR = "/tmp/music_ingest"


def ensure_job_temp_dir(job_id: str) -> str:
    path = os.path.join(BASE_TEMP_DIR, job_id)
    os.makedirs(path, exist_ok=True)
    return path
