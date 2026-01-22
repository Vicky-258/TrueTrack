import time
import logging
import threading
from typing import Optional
from datetime import datetime

from infra.job_store import JobStore
from core.pipeline_factory import create_pipeline
from core.pipeline import PipelineError
from core.states import PipelineState
from core.job import Job

# -------------------------------------------------
# Constants & Config
# -------------------------------------------------

WORKER_ID = "worker-1"          # later: uuid / hostname
POLL_INTERVAL_SECONDS = 0.5

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 5, 30]

logging.basicConfig(
    level=logging.INFO,
    format="[WORKER] %(asctime)s | %(levelname)s | %(message)s",
)

# -------------------------------------------------
# Worker (JOB LOGIC — UNCHANGED SEMANTICS)
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

    def __init__(self, store: JobStore, stop_event: threading.Event):
        self.store = store
        self.stop_event = stop_event

    def run_forever(self) -> None:
        logging.info("Worker started")

        while not self.stop_event.is_set():
            job = self._fetch_next_job()

            if not job:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            self._process_job(job)

        logging.info("Worker stopped gracefully")

    def _fetch_next_job(self) -> Optional[Job]:
        job_id = self.store.next_runnable()
        if not job_id:
            return None

        job = self.store.get(job_id)
        if not job:
            return None

        now = datetime.utcnow()

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

        # Reload job to catch external cancellation
        fresh = self.store.get(job.job_id)
        if not fresh:
            return

        job = fresh

        if job.current_state == PipelineState.CANCELLED:
            logging.info(f"Job {job.job_id} was cancelled before execution step")
            job.release_lock()
            self.store.update(job)
            return

        prev_state = job.current_state
        pipeline = create_pipeline()

        try:
            pipeline.step(job)

        except PipelineError as e:
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

            delay = BACKOFF_SECONDS[
                min(job.retry_count, len(BACKOFF_SECONDS) - 1)
            ]
            job.schedule_retry(delay)
            job.release_lock()
            self.store.update(job)

            logging.warning(
                f"Job {job.job_id} retry scheduled "
                f"in {delay}s (attempt {job.retry_count}/{MAX_RETRIES})"
            )
            return

        # Cancellation barrier BEFORE persisting new state
        fresh = self.store.get(job.job_id)
        if fresh and fresh.current_state == PipelineState.CANCELLED:
            logging.info(
                f"Job {job.job_id} cancelled during {prev_state.name}"
            )
            job.release_lock()
            self.store.update(fresh)
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
# WorkerRuntime (LIFECYCLE CONTROL ONLY)
# -------------------------------------------------

class WorkerRuntime:
    """
    Owns the lifecycle of the Worker.
    This is NOT job logic.
    """

    def __init__(self, store: JobStore):
        self.store = store
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread:
            return

        worker = Worker(self.store, self._stop_event)

        self._thread = threading.Thread(
            target=worker.run_forever,
            name="truetrack-worker",
            daemon=True,
        )
        self._thread.start()

        logging.info("WorkerRuntime started")

    def stop(self) -> None:
        if not self._thread:
            return

        logging.info("Stopping WorkerRuntime")
        self._stop_event.set()
        self._thread.join(timeout=5)

        logging.info("WorkerRuntime stopped")
