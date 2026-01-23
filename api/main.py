import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from api.models import (
    CreateJobRequest,
    JobStatusResponse,
    JobInputRequest,
)

from core.states import PipelineState
from core.job import Job, IdentityHint, JobOptions
from infra.sqlite_job_store import SQLiteJobStore
from infra.job_store import JobStore
from worker.runtime import WorkerRuntime
from dataclasses import asdict
from fastapi.responses import JSONResponse
import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles
from pathlib import Path


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

    if status == "success" and job.result:
        response.result = asdict(job.result)

    if status == "error":
        response.error = {
            "code": job.error_code,
            "message": job.error_message,
        }

    if job.final_metadata:
        response.final_metadata = job.final_metadata

    return response

def create_app(*, host: str, port: int) -> FastAPI:
    # ----------------------------------
    # Config
    # ----------------------------------
    
    api = APIRouter(prefix="/api")

    allowed_origins = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS",
            f"http://{host}:{port}",
        ).split(",")
    ]

    # ----------------------------------
    # Infra
    # ----------------------------------

    from core.config import Config
    
    db_path = str(Config.DB_PATH)
    store: JobStore = SQLiteJobStore(db_path)
    worker = WorkerRuntime(store)

    # ----------------------------------
    # Lifespan (worker ownership)
    # ----------------------------------

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker.start()
        yield
        worker.stop()

    app = FastAPI(
        title="TrueTrack API",
        lifespan=lifespan,
    )
    
    # ----------------------------------
    # Serve Next.js static assets
    # ----------------------------------
    
    NEXT_STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / ".next" / "static"
    
    if NEXT_STATIC_DIR.exists():
        app.mount(
            "/_next/static",
            StaticFiles(directory=NEXT_STATIC_DIR),
            name="next-static",
        )

    # ----------------------------------
    # Middleware
    # ----------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @api.post("/jobs", response_model=JobStatusResponse)
    def create_job(
        req: CreateJobRequest,
        idempotency_key: Optional[str] = Header(
            default=None, alias="Idempotency-Key"
        ),
    ):
        if idempotency_key:
            existing = store.get_job_by_idempotency_key(idempotency_key)
            if existing:
                return build_status(existing)

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
        
    @api.get("/jobs/{job_id}", response_model=JobStatusResponse)
    def get_job(job_id: str):
        job = store.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return build_status(job)

    @api.post("/jobs/{job_id}/input", response_model=JobStatusResponse)
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
                raise HTTPException(status_code = 400, detail = "Choice out of range")

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
                raise HTTPException(status_code = 400, detail = "Choice out of range")

            job.final_metadata = candidates[payload.choice]
            job.metadata_confidence = 100
            job.transition_to(PipelineState.TAGGING)

        else:
            raise HTTPException(status_code = 400, detail = "Invalid input state")

        store.update(job)
        return build_status(job)

    @api.post("/jobs/{job_id}/cancel", response_model=JobStatusResponse)
    def cancel_job(job_id: str):
        job = store.get(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        if job.current_state not in (
            PipelineState.FINALIZED,
            PipelineState.FAILED,
            PipelineState.CANCELLED,
        ):
            job.cancel()
            store.update(job)

        return build_status(job)

    @api.get("/jobs")
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

    @api.post("/jobs/{job_id}/resume", response_model=JobStatusResponse)
    def resume_job(job_id: str):
        job = store.get(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        if (
            job.current_state != PipelineState.CANCELLED
            and not job.current_state.name.startswith("USER_")
        ):
            raise HTTPException(status_code = 400, detail = "Job cannot be resumed")

        if not job.resume_from:
            raise HTTPException(status_code = 400, detail = "No resume point recorded")

        job.error_code = None
        job.error_message = None
        job.current_state = job.resume_from
        job.resume_from = None

        store.update(job)
        return build_status(job)
        
    @api.get("/__config", include_in_schema=False)
    def runtime_config():
        return JSONResponse({
            "api_base_url": f"http://{host}:{port}"
        })
    # ----------------------------------
    # Routes
    # ----------------------------------

    app.include_router(api)

    # ----------------------------------
    # Frontend Proxy (Next.js Standalone)
    # ----------------------------------
    
    NEXT_BASE = "http://127.0.0.1:3001"
    
    @app.api_route(
        "/{path:path}", 
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    )
    async def proxy_frontend(request: Request, path: str):
        url = f"{NEXT_BASE}/{path}" if path else f"{NEXT_BASE}/"
        
        req_headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length", "connection")
        }
        
        client = httpx.AsyncClient(follow_redirects=True)
        try:
            req = client.build_request(
                request.method, 
                url, 
                headers=req_headers,
                content=await request.body()
            )
            r = await client.send(req, stream=True)
            
            return StreamingResponse(
                r.aiter_bytes(),
                status_code=r.status_code,
                headers={
                    k: v for k, v in r.headers.items() 
                    if k.lower() not in ("content-encoding", "transfer-encoding", "connection")
                },
                background=BackgroundTask(client.aclose)
            )
        except Exception:
            await client.aclose()
            return JSONResponse({"error": "Frontend Unavailable"}, status_code=503)

    return app

