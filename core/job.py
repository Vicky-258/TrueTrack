from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import List, Optional, Dict, Any

from core.states import PipelineState


# =========================
# State Tracking
# =========================

@dataclass
class StateRecord:
    state: PipelineState
    entered_at: datetime
    exited_at: Optional[datetime] = None
    status: Optional[str] = None  # "success" | "failed"


# =========================
# Job Options
# =========================

@dataclass
class JobOptions:
    ask: bool = False
    force_archive: bool = False
    dry_run: bool = False
    flat: bool = False
    verbose: bool = False
    no_art: bool = False


# =========================
# Job Result
# =========================

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


# =========================
# Identity Hint
# =========================

@dataclass
class IdentityHint:
    title: str
    artists: list[str]
    album: str | None
    duration_ms: int | None

    video_id: str
    uploader: str | None

    confidence: int


# =========================
# Job Model
# =========================

@dataclass
class Job:
    options: JobOptions

    job_id: str = field(default_factory=lambda: str(uuid4()))
    raw_query: str = ""
    normalized_query: str = ""

    current_state: PipelineState = PipelineState.INIT
    state_history: List[StateRecord] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    failed_state: Optional[PipelineState] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    # ---------------------
    # Identity
    # ---------------------

    identity_hint: Optional[IdentityHint] = None
    identity_candidates: List[Dict[str, Any]] = field(default_factory=list)

    # ---------------------
    # Media
    # ---------------------

    source_candidates: List[Dict[str, Any]] = field(default_factory=list)
    selected_source: Optional[Dict[str, Any]] = None

    temp_dir: Optional[str] = None
    downloaded_file: Optional[str] = None
    extracted_file: Optional[str] = None

    # ---------------------
    # Metadata
    # ---------------------

    metadata_candidates: List[Dict[str, Any]] = field(default_factory=list)
    final_metadata: Optional[Dict[str, Any]] = None
    metadata_confidence: Optional[float] = None

    # ---------------------
    # Storage
    # ---------------------

    final_path: Optional[str] = None

    # ---------------------
    # Runtime
    # ---------------------

    last_message: Optional[str] = None
    result: JobResult = field(default_factory=JobResult)

    # =========================
    # Messaging
    # =========================

    def emit(self, message: str):
        self.last_message = message

    # =========================
    # State transitions
    # =========================

    def transition_to(self, new_state: PipelineState):
        now = datetime.utcnow()

        if self.state_history:
            self.state_history[-1].exited_at = now
            self.state_history[-1].status = "success"

        self.current_state = new_state
        self.state_history.append(
            StateRecord(state=new_state, entered_at=now)
        )
        self.updated_at = now

    def fail(self, error_code: str, error_message: str):
        now = datetime.utcnow()

        self.failed_state = self.current_state
        self.error_code = error_code
        self.error_message = error_message
        self.current_state = PipelineState.FAILED

        if self.state_history:
            self.state_history[-1].exited_at = now
            self.state_history[-1].status = "failed"

        self.result.error = error_message
        self.updated_at = now

    # =========================
    # Resume helpers (IMPORTANT)
    # =========================

    def apply_identity_choice(self, chosen: Dict[str, Any]):
        """
        Apply user-selected intent choice and resume pipeline.
        """
        self.identity_hint = IdentityHint(
            title=chosen["title"],
            artists=chosen.get("artists", []),
            album=chosen.get("album"),
            duration_ms=(chosen.get("duration") or 0) * 1000,
            video_id=chosen["video_id"],
            uploader=chosen.get("artists", [None])[0],
            confidence=100,  # user = ground truth
        )
        self.transition_to(PipelineState.SEARCHING)

    def apply_metadata_choice(self, idx: int):
        """
        Apply user-selected metadata choice and resume pipeline.
        """
        selected = self.metadata_candidates[idx]
        self.final_metadata = selected
        self.metadata_confidence = 100
        self.transition_to(PipelineState.TAGGING)
