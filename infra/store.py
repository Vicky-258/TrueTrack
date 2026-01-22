import os
from pathlib import Path
from infra.sqlite_job_store import SQLiteJobStore

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "jobs.db"

store = SQLiteJobStore(os.getenv("TRUETRACK_DB_PATH", str(DEFAULT_DB_PATH)))
