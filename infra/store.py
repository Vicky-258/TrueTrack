from core.config import Config
from infra.sqlite_job_store import SQLiteJobStore

store = SQLiteJobStore(str(Config.DB_PATH))
