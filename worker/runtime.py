import os
import time
import shutil
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

WORKER_ID = "worker-1"
POLL_INTERVAL_SECONDS = 0.5

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 5, 30]

logging.basicConfig(
    level=logging.INFO,
    format="[WORKER] %(asctime)s | %(levelname)s | %(message)s",
)


# -------------------------------------------------
# Worker
# -------------------------------------------------

class Worker:
    """
    Stateless pipeline executor.

    Guarantees:
    - Executes exactly ONE pipeline step per iteration
    - Never loops inside a job
    - Retries TRANSIENT failures with backoff
    - Moves to RETRY_PAUSED after max retries
    - Cleans temp only on true terminal states
    """

    def __init__(self, store: JobStore, stop_event: threading.Event):
        self.store = store
        self.stop_event = stop_event

    # -------------------------------------------------

    def run_forever(self) -> None:
        logging.info("Worker started")

        while not self.stop_event.is_set():
            job = self._fetch_next_job()

            if not job:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            self._process_job(job)

        logging.info("Worker stopped gracefully")

    # -------------------------------------------------

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
            f"(state={job.current_state.name})"
        )

        return job

    # -------------------------------------------------

    def _process_job(self, job: Job) -> None:
        fresh = self.store.get(job.job_id)
        if not fresh:
            return

        job = fresh

        if job.current_state == PipelineState.CANCELLED:
            self._release(job)
            logging.info(f"Job {job.job_id} cancelled")
            return

        prev_state = job.current_state
        pipeline = create_pipeline()

        try:
            pipeline.step(job)

        # -------------------------------------------------
        # Controlled Pipeline Failures
        # -------------------------------------------------

        except PipelineError as e:
            self._handle_pipeline_error(job, e, prev_state)
            return

        # -------------------------------------------------
        # Unexpected Failures
        # -------------------------------------------------

        except Exception as e:
            self._handle_unexpected_error(job, e)
            return

        # -------------------------------------------------
        # Success Path
        # -------------------------------------------------

        # Cancellation barrier
        fresh = self.store.get(job.job_id)
        if fresh and fresh.current_state == PipelineState.CANCELLED:
            self._release(fresh)
            logging.info(
                f"Job {job.job_id} cancelled during {prev_state.name}"
            )
            return

        self.store.update(job)

        # Terminal states
        if job.current_state in (
            PipelineState.FINALIZED,
            PipelineState.FAILED,
        ):
            self._cleanup_temp_dir(job)
            self._release(job)
            logging.info(
                f"Job {job.job_id} finished "
                f"(state={job.current_state.name})"
            )
            return

        # USER_* states
        if job.current_state.name.startswith("USER_"):
            self._release(job)
            logging.info(
                f"Job {job.job_id} waiting for user input "
                f"({job.current_state.name})"
            )
            return

        # Normal advancement
        self._release(job)
        logging.info(
            f"Job {job.job_id} advanced to {job.current_state.name}"
        )

    # -------------------------------------------------
    # Error Handling
    # -------------------------------------------------

    def _handle_pipeline_error(
        self,
        job: Job,
        error: PipelineError,
        prev_state: PipelineState,
    ) -> None:

        if error.category == "TRANSIENT":
            job.retry_count += 1

            if job.retry_count > MAX_RETRIES:
                job.resume_from = prev_state
                job.transition_to(PipelineState.RETRY_PAUSED)

                job.last_error_code = error.code
                job.last_error_message = error.message
                job.last_failed_state = prev_state.name

                logging.warning(
                    f"Job {job.job_id} paused after "
                    f"{MAX_RETRIES} transient failures"
                )
            else:
                delay = BACKOFF_SECONDS[
                    min(job.retry_count - 1, len(BACKOFF_SECONDS) - 1)
                ]
                job.schedule_retry(delay)

                logging.warning(
                    f"Job {job.job_id} transient error "
                    f"(attempt {job.retry_count}/{MAX_RETRIES}) "
                    f"retrying in {delay}s"
                )

            self._release(job)
            return

        # Permanent failure
        job.fail(
            error.code,
            error.message,
            category=error.category,
            tool=error.tool,
        )

        self._cleanup_temp_dir(job)
        self._release(job)

        logging.error(
            f"Job {job.job_id} failed permanently: "
            f"{error.code} | {error.message}"
        )

    # -------------------------------------------------

    def _handle_unexpected_error(self, job: Job, error: Exception) -> None:
        job.retry_count += 1

        if job.retry_count > MAX_RETRIES:
            job.fail("MAX_RETRIES_EXCEEDED", str(error))
            self._cleanup_temp_dir(job)
            self._release(job)

            logging.error(
                f"Job {job.job_id} failed after max retries"
            )
            return

        delay = BACKOFF_SECONDS[
            min(job.retry_count - 1, len(BACKOFF_SECONDS) - 1)
        ]
        job.schedule_retry(delay)

        self._release(job)

        logging.warning(
            f"Job {job.job_id} unexpected error "
            f"(attempt {job.retry_count}/{MAX_RETRIES}) "
            f"retrying in {delay}s"
        )

    # -------------------------------------------------

    def _release(self, job: Job) -> None:
        job.release_lock()
        self.store.update(job)

    # -------------------------------------------------

    def _cleanup_temp_dir(self, job: Job) -> None:
        if job.current_state not in (
            PipelineState.FINALIZED,
            PipelineState.FAILED,
        ):
            return

        if not job.temp_dir:
            return

        try:
            if os.path.exists(job.temp_dir):
                shutil.rmtree(job.temp_dir)
                logging.info(
                    f"Cleaned temp dir for job {job.job_id}"
                )
        except Exception as e:
            logging.error(
                f"Failed cleaning temp dir "
                f"{job.temp_dir}: {e}"
            )


# -------------------------------------------------
# WorkerRuntime
# -------------------------------------------------

class WorkerRuntime:
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