from typing import Callable, Dict, Literal
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import os

import shutil
import subprocess
import requests

from ytmusicapi import YTMusic
from mutagen.id3 import (
    ID3,
    TIT2, TPE1, TALB, TPE2,
    TRCK, TDRC, APIC,
)
from mutagen.mp3 import MP3

import sys
import importlib.util

from core.job import Job, IdentityHint
from core.states import PipelineState
from core.scoring import score_metadata

from utils.paths import ensure_job_temp_dir
from utils.metadata import search_itunes
from utils.storage import ensure_dir, safe_filename
from utils.tagging import fetch_album_art
from core.app_config import AppConfig


# =========================
# Errors
# =========================

class PipelineError(Exception):
    def __init__(self, code: str, message: str, category: Literal["TRANSIENT", "CONTENT", "DEPENDENCY"] | None = None, tool: str | None = None):
        self.code = code
        self.message = message
        self.category = category
        self.tool = tool  # Descriptive metadata only
        super().__init__(message)


# =========================
# Tool Resolution & Exec
# =========================

def _resolve_tool(
    tool_bin_name: str,
    python_module: str | None = None,
) -> tuple[list[str], str]:
    """
    Resolves a tool to a base command and source.
    """
    # 1. Try app-controlled environment (venv)
    if python_module:
        spec = importlib.util.find_spec(python_module)
        if spec:
            return [sys.executable, "-m", python_module], "venv"

    # 2. Fallback to system binary
    resolved_bin = shutil.which(tool_bin_name)
    if resolved_bin:
        return [resolved_bin], "system"

    # 3. Failure
    raise PipelineError(
        "EXTERNAL_TOOL_NOT_FOUND",
        f"Could not resolve tool '{tool_bin_name}' (module={python_module})"
    )


def _run_tool(
    job: Job,
    tool_bin_name: str,
    base_cmd: list[str],
    args: list[str],
    source: str,
    python_module: str | None,
    **kwargs
) -> None:
    """
    Executes a tool command and records metadata.
    """
    full_cmd = base_cmd + args
    
    # Record Metadata
    invocation_meta = {
        "tool": tool_bin_name,
        "source": source,
        "module": python_module,
        "cmd": full_cmd,
    }
    
    if not hasattr(job, "tool_invocations"):
        job.tool_invocations = []
    job.tool_invocations.append(invocation_meta)
    
    try:
        subprocess.run(
            full_cmd,
            check=True,
            **kwargs
        )
    except (subprocess.CalledProcessError, OSError) as e:
        raise PipelineError(
            "EXTERNAL_TOOL_ERROR",
            f"Execution of '{tool_bin_name}' failed: {str(e)}",
            tool=tool_bin_name
        ) from e


# =========================
# Pipeline Core (STEPPING)
# =========================

class Pipeline:
    """
    Headless, single-step state machine.

    Each call to `step(job)`:
    - Executes exactly ONE handler
    - Advances state OR pauses
    - Never blocks across states
    """

    def __init__(self):
        self.handlers: Dict[PipelineState, Callable[[Job], None]] = {}

    def register(self, state: PipelineState, handler: Callable[[Job], None]):
        self.handlers[state] = handler

    def step(self, job: Job):
        state = job.current_state

        # Terminal states
        if state in (PipelineState.FINALIZED, PipelineState.FAILED):
            return

        # Pause states (external controller must resume)
        if state.name.startswith("USER_"):
            return

        handler = self.handlers.get(state)
        if not handler:
            raise PipelineError(
                "NO_HANDLER",
                f"No handler registered for state {state.name}"
            )

        prev = job.current_state
        try:
            handler(job)
        except PipelineError:
            raise
        except Exception as e:
            raise PipelineError(
                "UNEXPECTED_ERROR",
                str(e)
            ) from e

        if job.current_state == prev:
            raise PipelineError(
                "NO_STATE_CHANGE",
                f"Handler for {state.name} did not advance state"
            )


# =========================
# Handlers
# =========================

def handle_init(job: Job):
    job.transition_to(PipelineState.RESOLVING_IDENTITY)


# -------------------------------------------------
# 1. RESOLVING_IDENTITY (YTMusic intent discovery)
# -------------------------------------------------

def handle_resolving_identity(job: Job):
    job.emit("Searching YouTube Music for matching tracks")

    ytmusic = YTMusic()
    try:
        results = ytmusic.search(job.raw_query, filter="songs")
    except Exception as e:
        raise PipelineError("YTMUSIC_ERROR", str(e))

    if not results:
        raise PipelineError("NO_RESULTS", "No songs found")

    candidates = []
    for r in results[:5]:
        candidates.append({
            "title": r.get("title"),
            "artists": [a["name"] for a in r.get("artists", [])],
            "album": r.get("album", {}).get("name"),
            "video_id": r.get("videoId"),
            "duration": r.get("duration_seconds"),
        })

    job.source_candidates = candidates

    if job.options.ask:
        job.transition_to(PipelineState.USER_INTENT_SELECTION)
        return

    chosen = candidates[0]
    job.identity_hint = IdentityHint(
        title=chosen["title"],
        artists=chosen["artists"],
        album=chosen["album"],
        duration_ms=(chosen["duration"] or 0) * 1000,
        video_id=chosen["video_id"],
        uploader=chosen["artists"][0] if chosen["artists"] else None,
        confidence=80,
    )

    job.transition_to(PipelineState.SEARCHING)


# -------------------------------------------------
# 2. USER_INTENT_SELECTION (PAUSE)
# -------------------------------------------------

def handle_user_intent_selection(job: Job):
    # Pause-only state; controller handles input
    return


# -------------------------------------------------
# 3. SEARCHING_MEDIA
# -------------------------------------------------

def handle_searching(job: Job):
    hint = job.identity_hint
    if not hint:
        raise PipelineError("NO_IDENTITY", "Missing identity hint")

    job.selected_source = {
        "url": f"https://www.youtube.com/watch?v={hint.video_id}",
        "title": hint.title,
        "duration": (hint.duration_ms or 0) // 1000,
        "uploader": hint.uploader,
    }

    job.transition_to(PipelineState.DOWNLOADING)


# -------------------------------------------------
# 4. DOWNLOADING
# -------------------------------------------------

def handle_downloading(job: Job):
    # 1. Pre-step Cleanup (Atomicity Illusion)
    # Ensure fresh start by wiping the step workspace
    temp_dir = ensure_job_temp_dir(job.job_id)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    job.temp_dir = str(temp_dir)

    # 2. Timestamp Recording (Start)
    if not hasattr(job, "step_started_at"):
        job.step_started_at = {}
    job.step_started_at[job.current_state.name] = datetime.now(timezone.utc)

    if job.options.dry_run:
        job.result.success = True
        job.result.title = job.identity_hint.title
        job.result.artist = ", ".join(job.identity_hint.artists)
        job.result.source = "dry-run"
        job.result.path = "(not written)"
        
        # Timestamp Recording (End - Dry Run)
        if not hasattr(job, "step_finished_at"):
            job.step_finished_at = {}
        job.step_finished_at[job.current_state.name] = datetime.now(timezone.utc)

        job.transition_to(PipelineState.FINALIZED)
        return

    job.emit(f"Downloading: {job.selected_source['title']}")

    # temp_dir is already set up and fresh
    output_template = str(temp_dir / "%(title)s.%(ext)s")

    args = [
        job.selected_source["url"],
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-quality", "0",
        "--output", output_template,
        "--quiet",
    ]

    try:
        base_cmd, source = _resolve_tool("yt-dlp", python_module="yt_dlp")
    except PipelineError as e:
        # Context: Tool resolution failed
        raise PipelineError(e.code, e.message, category="DEPENDENCY", tool="yt-dlp") from e

    try:
        _run_tool(
            job,
            tool_bin_name="yt-dlp",
            base_cmd=base_cmd,
            args=args,
            source=source,
            python_module="yt_dlp",
            stdout=None if job.options.verbose else subprocess.DEVNULL,
            stderr=None if job.options.verbose else subprocess.DEVNULL,
        )
    except PipelineError as e:
        # Context: Tool execution failed (likely content issue for yt-dlp)
        raise PipelineError(e.code, e.message, category="CONTENT", tool="yt-dlp") from e

    files = [p for p in temp_dir.iterdir() if p.is_file()]
    if not files:
        raise PipelineError("NO_FILE", "yt-dlp produced no output", category="CONTENT")

    job.downloaded_file = str(files[0])

    # 3. Timestamp Recording (End)
    if not hasattr(job, "step_finished_at"):
        job.step_finished_at = {}
    job.step_finished_at[job.current_state.name] = datetime.now(timezone.utc)

    job.transition_to(PipelineState.EXTRACTING)


# -------------------------------------------------
# 5. EXTRACTING
# -------------------------------------------------

def handle_extracting(job: Job):
    # 1. Pre-step Cleanup (Atomicity Illusion) with Input Preservation
    temp_dir = ensure_job_temp_dir(job.job_id)
    
    preserved_input_path = None
    backup_path = None

    # Check if we need to save the input file from the blast zone
    if job.downloaded_file:
        input_file = Path(job.downloaded_file)
        if input_file.exists() and temp_dir in input_file.parents:
            # Create a safe stash outside the blast zone
            backup_path = Path(tempfile.mkdtemp()) / input_file.name
            shutil.move(input_file, backup_path)
            preserved_input_path = input_file  # Remember where it was

    # Nuke it
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    job.temp_dir = str(temp_dir)

    # Restore logic
    if preserved_input_path and backup_path and backup_path.exists():
        # Ensure the subdirectory structure exists if it was deep (unlikely but safe)
        preserved_input_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(backup_path, preserved_input_path)
        shutil.rmtree(backup_path.parent) # Cleanup the stash dir

    # 2. Timestamp Recording (Start)
    if not hasattr(job, "step_started_at"):
        job.step_started_at = {}
    job.step_started_at[job.current_state.name] = datetime.now(timezone.utc)

    job.emit("Converting audio to MP3 (320kbps)")

    input_path = Path(job.downloaded_file)
    output_path = input_path.with_suffix(".mp3")

    args = ["-y", "-i", job.downloaded_file, "-ab", "320k", str(output_path)]
    
    try:
        base_cmd, source = _resolve_tool("ffmpeg")
        _run_tool(
            job,
            tool_bin_name="ffmpeg",
            base_cmd=base_cmd,
            args=args,
            source=source,
            python_module=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except PipelineError as e:
        # Context: Any failure in ffmpeg (resolution or exec) is DEPENDENCY
        raise PipelineError(e.code, e.message, category="DEPENDENCY", tool="ffmpeg") from e

    job.extracted_file = str(output_path)

    # 3. Timestamp Recording (End)
    if not hasattr(job, "step_finished_at"):
        job.step_finished_at = {}
    job.step_finished_at[job.current_state.name] = datetime.now(timezone.utc)

    job.transition_to(PipelineState.MATCHING_METADATA)


# -------------------------------------------------
# 6. MATCHING_METADATA
# -------------------------------------------------

def handle_matching_metadata(job: Job):
    job.emit("Searching iTunes for official metadata")

    if job.options.force_archive:
        job.transition_to(PipelineState.ARCHIVING)
        return

    hint = job.identity_hint
    try:
        results = search_itunes(hint.title, ", ".join(hint.artists))
    except requests.RequestException:
        job.emit("Metadata search failed (network error) — falling back to archive")
        job.transition_to(PipelineState.ARCHIVING)
        return

    if not results:
        job.transition_to(PipelineState.ARCHIVING)
        return

    scored = []
    for r in results:
        score, _ = score_metadata(
            r,
            hint.title,
            ", ".join(hint.artists),
            (hint.duration_ms or 0) // 1000,
        )
        r["_score"] = score
        scored.append(r)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    job.metadata_candidates = scored
    job.final_metadata = scored[0]
    job.metadata_confidence = scored[0]["_score"]

    if job.metadata_confidence < 60:
        job.transition_to(PipelineState.USER_METADATA_SELECTION)
        return

    job.transition_to(PipelineState.TAGGING)


# -------------------------------------------------
# 7. USER_METADATA_SELECTION (PAUSE)
# -------------------------------------------------

def handle_metadata_user_selection(job: Job):
    return


# -------------------------------------------------
# 8. TAGGING
# -------------------------------------------------

def handle_tagging(job: Job):
    job.emit("Embedding metadata and album art")

    meta = job.final_metadata
    audio = MP3(job.extracted_file, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=meta["trackName"]))
    audio.tags.add(TPE1(encoding=3, text=meta["artistName"]))
    audio.tags.add(TALB(encoding=3, text=meta["collectionName"]))

    if meta.get("trackNumber"):
        audio.tags.add(TRCK(encoding=3, text=str(meta["trackNumber"])))

    if meta.get("releaseDate"):
        audio.tags.add(TDRC(encoding=3, text=meta["releaseDate"][:4]))

    try:
        art = fetch_album_art(meta)
        if art:
            audio.tags.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=art,
            ))
    except requests.RequestException:
        pass

    audio.save()
    job.transition_to(PipelineState.STORING)


# -------------------------------------------------
# 9. STORING
# -------------------------------------------------

def handle_storage(job: Job):
    job.emit("Saving track to music library")

    library_root = AppConfig.get_music_library_root()
    ensure_dir(library_root)

    title = safe_filename(job.final_metadata["trackName"])
    artist = safe_filename(job.final_metadata["artistName"])
    final_path = library_root / f"{title} - {artist}.mp3"

    if final_path.exists():
        job.result.success = True
        job.result.title = title
        job.result.artist = artist
        job.result.album = job.final_metadata.get("collectionName")
        job.result.source = "library"
        job.result.path = str(final_path)
        job.result.reason = "already_exists"
    
        job.transition_to(PipelineState.FINALIZED)
        return

    shutil.move(job.extracted_file, final_path)

    job.result.success = True
    job.result.title = title
    job.result.artist = artist
    job.result.album = job.final_metadata.get("collectionName")
    job.result.source = "iTunes (verified)"
    job.result.path = str(final_path)

    job.transition_to(PipelineState.FINALIZED)


# -------------------------------------------------
# 10. ARCHIVING
# -------------------------------------------------

def handle_archiving(job: Job):
    job.emit("No reliable metadata found — archiving track")

    library_root = AppConfig.get_music_library_root()
    archive_dir = library_root / "_Unidentified"
    ensure_dir(archive_dir)

    hint = job.identity_hint
    title = safe_filename(hint.title)
    artist = safe_filename(hint.artists[0] if hint.artists else "Unknown")

    final_path = archive_dir / f"{title} - {artist}.mp3"
    shutil.move(job.extracted_file, final_path)

    job.result.archived = True
    job.result.title = hint.title
    job.result.artist = ", ".join(hint.artists)
    job.result.reason = "Unverified metadata"
    job.result.path = str(final_path)

    job.transition_to(PipelineState.FINALIZED)
