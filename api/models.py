from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal

class JobOptions(BaseModel):
    ask: bool = Field(
        default=False,
        description="Pause for user intent selection when multiple sources are found"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose pipeline logging"
    )
    dry_run: bool = Field(
        default=False,
        description="Skip downloads and file writes"
    )
    force_archive: bool = Field(
        default=False,
        description="Skip metadata matching and archive the track"
    )

class CreateJobRequest(BaseModel):
    query: str = Field(
        ...,
        description="Raw user query (song name, artist, etc.)"
    )
    options: JobOptions

class JobInputRequest(BaseModel):
    choice: int = Field(
        ...,
        ge=0,
        description="Index of the selected choice"
    )

class JobStatusResponse(BaseModel):
    job_id: str
    state: str

    status: Literal[
        "running",
        "waiting",
        "success",
        "error",
        "cancelled"
    ]

    input_required: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Present only when user input is required"
    )

    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Present only when job is finalized successfully"
    )

    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Present only when job has failed"
    )
    
    final_metadata: Optional[Dict[str, Any]] = None
    can_resume: bool = False

class JobSummaryResponse(BaseModel):
    job_id: str
    status: str
    state: str
    title: Optional[str] = None
    artist: Optional[str] = None
    created_at: str
    can_resume: bool = False


class UpdateMusicLibraryRequest(BaseModel):
    path: str = Field(
        ...,
        description="Absolute path to the new music library root"
    )

class SettingsResponse(BaseModel):
    music_library_path: str
    source: Literal["db", "env", "default"]
