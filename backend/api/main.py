from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from api.models import (
    CreateJobRequest,
    JobStatusResponse,
    JobInputRequest,
    JobSummaryResponse
)
from core.states import PipelineState
from core.job import Job, IdentityHint
from infra.sqlite_job_store import SQLiteJobStore
from core.job import JobOptions
from typing import Optional
from infra.store import store
from dataclasses import asdict

app = FastAPI(title="TrueTracks API")

allow_origins=["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_status(job: Job) -> JobStatusResponse:
    status = "running"

    if job.current_state.name.startswith("USER_"):
        status = "waiting"

    if job.current_state == PipelineState.FINALIZED:
        status = "success"

    if job.current_state == PipelineState.FAILED:
        status = "error"
        
    if job.current_state == PipelineState.CANCELLED:
        status = "cancelled"

    can_resume = (
        job.current_state == PipelineState.CANCELLED
        and job.resume_from is not None
    )
    
    response = JobStatusResponse(
        job_id=job.job_id,
        state=job.current_state.name,
        status=status,
        can_resume=can_resume,
    )

    if status == "waiting":
        response.input_required = {
            "type": job.current_state.name.lower(),
            "choices": job.metadata_candidates or job.source_candidates,
        }

    if status == "success":
        response.result = asdict(job.result)


    if status == "error":
        response.error = {
            "code": job.error_code,
            "message": job.error_message,
        }
        
    # Expose metadata once available
    if job.final_metadata:
        response.final_metadata = job.final_metadata

    return response

@app.post("/jobs", response_model=JobStatusResponse)
def create_job(
    req: CreateJobRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    # ----------------------------------
    # Idempotency check
    # ----------------------------------

    if idempotency_key:
        existing = store.get_job_by_idempotency_key(idempotency_key)
        if existing:
            return build_status(existing)

    # ----------------------------------
    # Create new job
    # ----------------------------------

    job = Job(
        raw_query=req.query,
        normalized_query=req.query.lower(),
        options=JobOptions(**req.options.dict()),
    )

    job.transition_to(PipelineState.RESOLVING_IDENTITY)
    store.create(job)

    if idempotency_key:
        store.bind_idempotency_key(idempotency_key, job.job_id)

    return build_status(job)

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_status(job)

@app.post("/jobs/{job_id}/input", response_model=JobStatusResponse)
def provide_input(job_id: str, payload: JobInputRequest):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    state = job.current_state

    if not state.name.startswith("USER_"):
        raise HTTPException(
            status_code=400,
            detail="Job is not waiting for user input",
        )
    if state == PipelineState.USER_INTENT_SELECTION:
        candidates = job.source_candidates

        if payload.choice < 0 or payload.choice >= len(candidates):
            raise HTTPException(status_code=400, detail="Choice out of range")

        selected = candidates[payload.choice]

        job.identity_hint = IdentityHint(
            title=selected["title"],
            artists=selected["artists"],
            album=selected.get("album"),
            duration_ms=(selected.get("duration") or 0) * 1000,
            video_id=selected.get("video_id"),
            uploader=selected["artists"][0] if selected["artists"] else None,
            confidence=80,
        )

        job.transition_to(PipelineState.SEARCHING)
        
    elif state == PipelineState.USER_METADATA_SELECTION:
        candidates = job.metadata_candidates

        if payload.choice < 0 or payload.choice >= len(candidates):
            raise HTTPException(status_code=400, detail="Choice out of range")

        selected = candidates[payload.choice]

        job.final_metadata = selected
        job.metadata_confidence = 100
        job.transition_to(PipelineState.TAGGING)

    else:
        raise HTTPException(status_code=400, detail="Invalid input state")

    store.update(job)

    # DO NOT execute pipeline
    return build_status(job)

@app.post("/jobs/{job_id}/cancel", response_model=JobStatusResponse)
def cancel_job(job_id: str):
    job = store.get(job_id)
    print("resume_from =", job.resume_from)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.current_state in (
        PipelineState.FINALIZED,
        PipelineState.FAILED,
        PipelineState.CANCELLED,
    ):
        return build_status(job)

    job.cancel()
    store.update(job)

    return build_status(job)

@app.get("/jobs")
def list_jobs():
    jobs = store.list_jobs(limit=50)

    summaries = []
    for job in jobs:
        title = None
        artist = None

        if job.final_metadata:
            title = job.final_metadata.get("trackName")
            artist = job.final_metadata.get("artistName")
        elif job.result:
            title = job.result.title
            artist = job.result.artist

        summaries.append({
            "job_id": job.job_id,
            "status": (
                "success"
                if job.current_state == PipelineState.FINALIZED
                else job.current_state.name.lower()
            ),
            "state": job.current_state.name,
            "title": title,
            "artist": artist,
            "created_at": job.created_at.isoformat(),
            "can_resume": (
                job.current_state == PipelineState.CANCELLED
                and job.resume_from is not None
            ),
        })

    return summaries

@app.post("/jobs/{job_id}/resume", response_model=JobStatusResponse)
def resume_job(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Only allow resume from CANCELLED or USER_* states
    if job.current_state != PipelineState.CANCELLED and not job.current_state.name.startswith("USER_"):
        raise HTTPException(
            status_code=400,
            detail="Job cannot be resumed from this state",
        )

    if not job.resume_from:
        raise HTTPException(
            status_code=400,
            detail="No resume point recorded",
        )

    # Clear cancellation markers
    job.error_code = None
    job.error_message = None

    # Restore intent (restart risky states safely)
    job.current_state = job.resume_from
    job.resume_from = None

    store.update(job)
    return build_status(job)
