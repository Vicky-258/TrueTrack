import time
import logging
from typing import Optional

from infra.job_store import JobStore
from core.pipeline_factory import create_pipeline
from core.pipeline import PipelineError
from core.states import PipelineState
from core.job import Job
from infra.sqlite_job_store import SQLiteJobStore
from datetime import datetime

WORKER_ID = "worker-1"  # later: uuid / hostname
LOCK_TTL_SECONDS = 60

# -------------------------------------------------
# Config
# -------------------------------------------------

POLL_INTERVAL_SECONDS = 0.5
WORKER_ID = "worker-1"  # later: uuid / hostname

logging.basicConfig(
    level=logging.INFO,
    format="[WORKER] %(asctime)s | %(levelname)s | %(message)s",
)

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 5, 30]

# -------------------------------------------------
# Worker
# -------------------------------------------------

class Worker:
    """
    Stateless pipeline executor.

    Responsibilities:
    - pick runnable jobs
    - execute exactly ONE pipeline step
    - persist job state
    - respect USER_* pauses
    """

    def __init__(self, store: JobStore):
        self.store = store

    def run_forever(self):
        logging.info("Worker started")

        while True:
            job = self._fetch_next_job()

            if not job:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            self._process_job(job)

    def _fetch_next_job(self) -> Optional[Job]:
        job_id = self.store.next_runnable()
        if not job_id:
            return None

        job = self.store.get(job_id)
        if not job:
            return None

        now = datetime.utcnow()

        # Acquire lock
        job.acquire_lock(WORKER_ID, now)
        self.store.update(job)

        logging.info(
            f"Picked job {job.job_id} "
            f"(state={job.current_state.name}, locked_by={WORKER_ID})"
        )
        return job

    def _process_job(self, job: Job) -> None:
        """
        Execute exactly ONE pipeline step for a locked job.
    
        Invariants:
        - job is already locked by this worker
        - exactly one pipeline.step() call
        - lock is ALWAYS released before return
        """
    
        prev_state = job.current_state
        pipeline = create_pipeline()
    
        try:
            pipeline.step(job)
    
        except PipelineError as e:
            # Deterministic, domain-defined failure
            job.fail(e.code, e.message)
            job.release_lock()
            self.store.update(job)
    
            logging.error(
                f"Job {job.job_id} failed: {e.code} | {e.message}"
            )
            return
    
        except Exception as e:
            if job.retry_count >= MAX_RETRIES:
                job.fail("MAX_RETRIES_EXCEEDED", str(e))
                job.release_lock()
                self.store.update(job)
        
                logging.error(
                    f"Job {job.job_id} failed after max retries"
                )
                return
        
            delay = BACKOFF_SECONDS[min(job.retry_count, len(BACKOFF_SECONDS) - 1)]
            job.schedule_retry(delay)
            job.release_lock()
            self.store.update(job)
        
            logging.warning(
                f"Job {job.job_id} retry scheduled "
                f"in {delay}s (attempt {job.retry_count}/{MAX_RETRIES})"
            )
            return
    
        # Persist successful step
        self.store.update(job)
    
        # -------------------------------------------------
        # Stop conditions (NO LOOPS)
        # -------------------------------------------------
    
        if job.current_state == prev_state:
            job.release_lock()
            self.store.update(job)
    
            logging.warning(
                f"Job {job.job_id} did not advance state "
                f"({job.current_state.name})"
            )
            return
    
        if job.current_state.name.startswith("USER_"):
            job.release_lock()
            self.store.update(job)
    
            logging.info(
                f"Job {job.job_id} waiting for user input "
                f"({job.current_state.name})"
            )
            return
    
        if job.current_state in (
            PipelineState.FINALIZED,
            PipelineState.FAILED,
        ):
            job.release_lock()
            self.store.update(job)
    
            logging.info(
                f"Job {job.job_id} finished "
                f"(state={job.current_state.name})"
            )
            return
    
        # -------------------------------------------------
        # Continue later (lock released, job re-eligible)
        # -------------------------------------------------
    
        job.release_lock()
        self.store.update(job)
    
        logging.info(
            f"Job {job.job_id} advanced to {job.current_state.name}"
        )

# -------------------------------------------------
# Entrypoint
# -------------------------------------------------

def main():

    store = SQLiteJobStore("jobs.db")

    worker = Worker(store)
    worker.run_forever()


if __name__ == "__main__":
    main()
