from pathlib import Path
from infra.sqlite_job_store import SQLiteJobStore

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "jobs.db"

store = SQLiteJobStore(str(DB_PATH))
