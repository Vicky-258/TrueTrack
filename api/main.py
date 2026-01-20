from fastapi import FastAPI, HTTPException
from api.models import (
    CreateJobRequest,
    JobStatusResponse,
    JobInputRequest,
)
from api.store import JOBS
from core.job import Job
from core.states import PipelineState
from core.pipeline_factory import create_pipeline
from core.job import IdentityHint

app = FastAPI(title="TrueTracks API")

def drive_pipeline(job: Job):
    pipeline = create_pipeline()

    while True:
        prev = job.current_state
        pipeline.step(job)

        # Stop conditions
        if job.current_state == prev:
            break

        if job.current_state.name.startswith("USER_"):
            break

        if job.current_state in (
            PipelineState.FINALIZED,
            PipelineState.FAILED,
        ):
            break

def build_status(job: Job) -> JobStatusResponse:
    response = JobStatusResponse(
        job_id=job.job_id,
        state=job.current_state.name,
        status="running",
    )

    if job.current_state.name.startswith("USER_"):
        response.status = "waiting"
        response.input_required = {
            "type": job.current_state.name.lower(),
            "choices": job.metadata_candidates or job.source_candidates,
        }

    if job.current_state == PipelineState.FINALIZED:
        response.status = "success"
        response.result = job.result.to_dict()

    if job.current_state == PipelineState.FAILED:
        response.status = "error"
        response.error = {
            "code": job.error_code,
            "message": job.error_message,
        }

    return response

@app.post("/jobs", response_model=JobStatusResponse)
def create_job(req: CreateJobRequest):
    job = Job(
        raw_query=req.query,
        normalized_query=req.query.lower(),
        options=req.options,
    )

    JOBS[job.job_id] = job

    drive_pipeline(job)

    return build_status(job)

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_status(job)

@app.post("/jobs/{job_id}/input", response_model=JobStatusResponse)
def provide_input(job_id: str, payload: JobInputRequest):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    state = job.current_state

    if not state.name.startswith("USER_"):
        raise HTTPException(
            status_code=400,
            detail="Job is not waiting for user input",
        )

    # -------------------------------
    # USER_INTENT_SELECTION
    # -------------------------------
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


    # -------------------------------
    # USER_METADATA_SELECTION
    # -------------------------------
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

    # Resume pipeline
    drive_pipeline(job)

    return build_status(job)

