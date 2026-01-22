from abc import ABC, abstractmethod
from typing import Optional, Iterable, Dict
from datetime import datetime

from core.job import Job
from core.states import PipelineState

class JobStore(ABC):
    """
    Abstract persistence interface for Jobs.
    """

    @abstractmethod
    def create(self, job: Job) -> None:
        """Persist a newly created job."""
        raise NotImplementedError

    @abstractmethod
    def get(self, job_id: str) -> Optional[Job]:
        raise NotImplementedError

    @abstractmethod
    def update(self, job: Job) -> None:
        raise NotImplementedError

    @abstractmethod
    def next_runnable(self) -> Optional[str]:
        raise NotImplementedError

    def list(self) -> Iterable[str]:
        return []

def is_runnable(job: Job) -> bool:
    if job.current_state in (PipelineState.FINALIZED, PipelineState.FAILED):
        return False

    if job.current_state.name.startswith("USER_"):
        return False

    return True

class InMemoryJobStore(JobStore):
    """
    In-memory JobStore.

    ⚠️ Not crash-safe.
    ✅ Correct by contract.
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._queue: list[str] = []

    def create(self, job: Job) -> None:
        if job.job_id in self._jobs:
            raise ValueError(f"Job {job.job_id} already exists")

        now = datetime.utcnow()
        job.created_at = now
        job.updated_at = now

        self._jobs[job.job_id] = job
        self._queue.append(job.job_id)

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update(self, job: Job) -> None:
        if job.job_id not in self._jobs:
            raise KeyError(f"Job {job.job_id} does not exist")

        job.updated_at = datetime.utcnow()
        self._jobs[job.job_id] = job

        if is_runnable(job):
            self._queue.append(job.job_id)

    def next_runnable(self) -> Optional[str]:
        while self._queue:
            job_id = self._queue.pop(0)
            job = self._jobs.get(job_id)

            if job is None:
                continue

            if is_runnable(job):
                return job_id

        return None

    def list(self) -> Iterable[str]:
        return list(self._jobs.keys())
