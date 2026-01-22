from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Optional, List, Dict, Any

from core.states import PipelineState

@dataclass
class StateRecord:
    state: PipelineState
    entered_at: datetime
    exited_at: Optional[datetime] = None
    status: Optional[str] = None  # "success" | "failed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.name,
            "entered_at": self.entered_at.isoformat(),
            "exited_at": self.exited_at.isoformat() if self.exited_at else None,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateRecord":
        return cls(
            state=PipelineState[data["state"]],
            entered_at=datetime.fromisoformat(data["entered_at"]),
            exited_at=datetime.fromisoformat(data["exited_at"])
            if data.get("exited_at") else None,
            status=data.get("status"),
        )

@dataclass
class JobOptions:
    ask: bool = False
    force_archive: bool = False
    dry_run: bool = False
    flat: bool = False
    verbose: bool = False
    no_art: bool = False

@dataclass
class JobResult:
    success: bool = False
    archived: bool = False

    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

    source: Optional[str] = None
    path: Optional[str] = None
    reason: Optional[str] = None
    error: Optional[str] = None

@dataclass
class IdentityHint:
    title: str
    artists: List[str]
    album: Optional[str]
    duration_ms: Optional[int]

    video_id: str
    uploader: Optional[str]

    confidence: int

MAX_STATE_HISTORY = 50

@dataclass
class Job:
    job_id: str = field(default_factory=lambda: str(uuid4()))

    raw_query: str = ""
    normalized_query: str = ""
    options: JobOptions = field(default_factory=JobOptions)

    current_state: PipelineState = PipelineState.INIT
    state_history: List[StateRecord] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    failed_state: Optional[PipelineState] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    identity_hint: Optional[IdentityHint] = None
    source_candidates: List[Dict[str, Any]] = field(default_factory=list)

    selected_source: Optional[Dict[str, Any]] = None
    temp_dir: Optional[str] = None
    downloaded_file: Optional[str] = None
    extracted_file: Optional[str] = None

    metadata_candidates: List[Dict[str, Any]] = field(default_factory=list)
    final_metadata: Optional[Dict[str, Any]] = None
    metadata_confidence: Optional[float] = None

    final_path: Optional[str] = None
    result: JobResult = field(default_factory=JobResult)

    last_message: Optional[str] = None

    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None

    next_run_at: Optional[datetime] = None
    
    resume_from: Optional[PipelineState] = None

    def emit(self, message: str) -> None:
        self.last_message = message

    def transition_to(self, new_state: PipelineState) -> None:
        now = datetime.utcnow()

        if self.state_history:
            self.state_history[-1].exited_at = now
            self.state_history[-1].status = "success"

        self.current_state = new_state
        self.state_history.append(StateRecord(new_state, now))

        if len(self.state_history) > MAX_STATE_HISTORY:
            self.state_history.pop(0)

        self.updated_at = now

    def fail(self, code: str, message: str) -> None:
        now = datetime.utcnow()

        self.failed_state = self.current_state
        self.error_code = code
        self.error_message = message
        self.current_state = PipelineState.FAILED

        if self.state_history:
            self.state_history[-1].exited_at = now
            self.state_history[-1].status = "failed"

        self.result.error = message
        self.updated_at = now

    def cancel(self, reason: str = "Cancelled by user") -> None:
        if self.current_state not in (
            PipelineState.FINALIZED,
            PipelineState.FAILED,
            PipelineState.CANCELLED,
        ):
            self.resume_from = self.current_state
    
        self.release_lock()
        self.transition_to(PipelineState.CANCELLED)
        self.error_code = "CANCELLED"
        self.error_message = reason
        self.result.error = reason

    def is_locked(self, now: datetime, ttl_seconds: int) -> bool:
        return bool(
            self.locked_at and
            (now - self.locked_at).total_seconds() < ttl_seconds
        )

    def acquire_lock(self, worker_id: str, now: datetime) -> None:
        self.locked_at = now
        self.locked_by = worker_id
        self.updated_at = now

    def release_lock(self) -> None:
        self.locked_at = None
        self.locked_by = None

    def schedule_retry(self, delay_seconds: int) -> None:
        self.retry_count += 1
        self.next_run_at = datetime.utcnow() + timedelta(seconds=delay_seconds)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "options": asdict(self.options),

            "current_state": self.current_state.name,
            "state_history": [s.to_dict() for s in self.state_history],

            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),

            "failed_state": self.failed_state.name if self.failed_state else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,

            "identity_hint": asdict(self.identity_hint) if self.identity_hint else None,
            "source_candidates": self.source_candidates,

            "selected_source": self.selected_source,
            "temp_dir": self.temp_dir,
            "downloaded_file": self.downloaded_file,
            "extracted_file": self.extracted_file,

            "metadata_candidates": self.metadata_candidates,
            "final_metadata": self.final_metadata,
            "metadata_confidence": self.metadata_confidence,

            "final_path": self.final_path,
            "result": asdict(self.result),

            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "locked_by": self.locked_by,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            
            "resume_from": self.resume_from.name if self.resume_from else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        job = cls(
            job_id=data["job_id"],
            raw_query=data.get("raw_query", ""),
            normalized_query=data.get("normalized_query", ""),
            options=JobOptions(**data.get("options", {})),
        )

        job.current_state = PipelineState[data["current_state"]]
        job.state_history = [
            StateRecord.from_dict(s)
            for s in data.get("state_history", [])
        ]

        job.created_at = datetime.fromisoformat(data["created_at"])
        job.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("failed_state"):
            job.failed_state = PipelineState[data["failed_state"]]

        job.error_code = data.get("error_code")
        job.error_message = data.get("error_message")
        job.retry_count = data.get("retry_count", 0)

        if data.get("identity_hint"):
            job.identity_hint = IdentityHint(**data["identity_hint"])

        if data.get("locked_at"):
            job.locked_at = datetime.fromisoformat(data["locked_at"])

        job.locked_by = data.get("locked_by")

        if data.get("next_run_at"):
            job.next_run_at = datetime.fromisoformat(data["next_run_at"])
            
        if data.get("resume_from"):
            job.resume_from = PipelineState[data["resume_from"]]

        job.source_candidates = data.get("source_candidates", [])
        job.selected_source = data.get("selected_source")

        job.temp_dir = data.get("temp_dir")
        job.downloaded_file = data.get("downloaded_file")
        job.extracted_file = data.get("extracted_file")

        job.metadata_candidates = data.get("metadata_candidates", [])
        job.final_metadata = data.get("final_metadata")
        job.metadata_confidence = data.get("metadata_confidence")

        job.final_path = data.get("final_path")
        job.result = JobResult(**data.get("result", {}))

        return job

