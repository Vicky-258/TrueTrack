import sqlite3
import json
from typing import Optional, Iterable
from datetime import datetime

from infra.job_store import JobStore
from core.job import Job
from core.states import PipelineState

LOCK_TTL_SECONDS = 60

def is_runnable(job: Job) -> bool:
    if job.current_state in (
        PipelineState.FINALIZED,
        PipelineState.FAILED,
        PipelineState.CANCELLED,
    ):
        return False

    if job.current_state.name.startswith("USER_"):
        return False

    now = datetime.utcnow()

    if job.next_run_at and job.next_run_at > now:
        return False

    if job.is_locked(now, LOCK_TTL_SECONDS):
        return False

    return True
    
class SQLiteJobStore(JobStore):
    """
    SQLite-backed JobStore.

    Properties:
    - shared across processes
    - crash-safe
    - resumable
    - supports job locking
    - supports idempotency
    """

    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()

    def create(self, job: Job) -> None:
        payload = json.dumps(job.to_dict())
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO jobs (job_id, data, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (job.job_id, payload, now),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError(f"Job {job.job_id} already exists")

    def get(self, job_id: str) -> Optional[Job]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()

        if not row:
            return None

        return Job.from_dict(json.loads(row[0]))

    def update(self, job: Job) -> None:
        payload = json.dumps(job.to_dict())
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                UPDATE jobs
                SET data = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (payload, now, job.job_id),
            )

            if cur.rowcount == 0:
                raise KeyError(f"Job {job.job_id} does not exist")

            conn.commit()

    def next_runnable(self) -> Optional[str]:
        """
        Return the job_id of the next runnable job.

        Ordering:
        - oldest updated first (fairness)
        """

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT job_id, data
                FROM jobs
                ORDER BY updated_at ASC
                """
            ).fetchall()

        for job_id, raw in rows:
            job = Job.from_dict(json.loads(raw))
            if is_runnable(job):
                return job_id

        return None

    def list(self) -> Iterable[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT job_id FROM jobs"
            ).fetchall()

        return [row[0] for row in rows]

    def get_job_by_idempotency_key(self, key: str) -> Optional[Job]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT job_id FROM idempotency_keys WHERE key = ?",
                (key,),
            ).fetchone()

        if not row:
            return None

        return self.get(row[0])

    def bind_idempotency_key(self, key: str, job_id: str) -> None:
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO idempotency_keys (key, job_id, created_at)
                VALUES (?, ?, ?)
                """,
                (key, job_id, now),
            )
            conn.commit()