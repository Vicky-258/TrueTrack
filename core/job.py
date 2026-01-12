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
    # outcome
    success: bool = False
    archived: bool = False

    # identity
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

    # metadata
    source: Optional[str] = None   # e.g. "iTunes (verified)"

    # storage
    path: Optional[str] = None

    # diagnostics
    reason: Optional[str] = None   # archive reason
    error: Optional[str] = None    # failure reason

    
@dataclass
class IdentityHint:
    title: str
    artists: list[str]
    album: str | None
    duration_ms: int | None

    # source consistency
    video_id: str
    uploader: str | None

    confidence: int


# =========================
# Job Model
# =========================

@dataclass
class Job:
    options: JobOptions
    state: PipelineState = PipelineState.INIT
    # ---- identity ----
    job_id: str = field(default_factory=lambda: str(uuid4()))
    raw_query: str = ""
    normalized_query: str = ""

    # ---- pipeline state ----
    current_state: PipelineState = PipelineState.INIT
    state_history: List[StateRecord] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ---- failure ----
    failed_state: Optional[PipelineState] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    # =====================================================
    # 1. IDENTITY (YTMusic heuristic — NOT canonical)
    # =====================================================
    identity_hint: IdentityHint | None = None
    # expected shape:
    # {
    #   "title": str,
    #   "artists": list[str],
    #   "album": str | None,
    #   "duration_ms": int | None,
    #   "video_id": str,
    # }

    # =====================================================
    # 2. MEDIA (YouTube / yt-dlp)
    # =====================================================
    source_candidates: List[Dict[str, Any]] = field(default_factory=list)
    selected_source: Optional[Dict[str, Any]] = None
    
    identity_candidates: list[dict] = field(default_factory=list)

    temp_dir: Optional[str] = None
    downloaded_file: Optional[str] = None
    extracted_file: Optional[str] = None

    # =====================================================
    # 3. METADATA (iTunes canonical)
    # =====================================================
    metadata_candidates: List[Dict[str, Any]] = field(default_factory=list)
    final_metadata: Optional[Dict[str, Any]] = None
    metadata_confidence: Optional[float] = None

    # =====================================================
    # 4. STORAGE
    # =====================================================
    final_path: Optional[str] = None
    
    last_message: Optional[str] = None
    
    result: JobResult = field(default_factory=JobResult)


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

        self.updated_at = now
