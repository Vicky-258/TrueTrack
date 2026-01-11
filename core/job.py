from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import List, Optional
from typing import Dict, Any

from core.states import PipelineState

@dataclass
class StateRecord:
    state: PipelineState
    entered_at: datetime
    exited_at: Optional[datetime] = None
    status: Optional[str] = None  # "success" | "failed"


@dataclass
class Job:
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
    
    source_candidates: list[dict] = field(default_factory=list)
    selected_source: dict | None = None
    
    temp_dir: str | None = None
    downloaded_file: str | None = None
    extracted_file: str | None = None
    
    metadata_candidates: list[dict] = field(default_factory=list)
    final_metadata: dict | None = None
    metadata_confidence: float | None = None
    
    final_path: str | None = None


    def transition_to(self, new_state: PipelineState):
        now = datetime.utcnow()

        # close previous state
        if self.state_history:
            self.state_history[-1].exited_at = now
            self.state_history[-1].status = "success"

        # enter new state
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
