from typing import Callable, Dict
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

from core.job import Job, IdentityHint
from core.states import PipelineState
from core.scoring import score_metadata

from utils.paths import ensure_job_temp_dir
from utils.metadata import search_itunes
from utils.storage import ensure_dir, safe_filename, LIBRARY_ROOT
from utils.tagging import fetch_album_art


# =========================
# Errors
# =========================

class PipelineError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


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
        handler(job)

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
    if job.options.dry_run:
        job.result.success = True
        job.result.title = job.identity_hint.title
        job.result.artist = ", ".join(job.identity_hint.artists)
        job.result.source = "dry-run"
        job.result.path = "(not written)"
        job.transition_to(PipelineState.FINALIZED)
        return

    job.emit(f"Downloading: {job.selected_source['title']}")

    temp_dir = ensure_job_temp_dir(job.job_id)
    job.temp_dir = temp_dir

    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        job.selected_source["url"],
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-quality", "0",
        "--output", output_template,
        "--quiet",
    ]

    subprocess.run(
        cmd,
        check=True,
        stdout=None if job.options.verbose else subprocess.DEVNULL,
        stderr=None if job.options.verbose else subprocess.DEVNULL,
    )

    files = os.listdir(temp_dir)
    if not files:
        raise PipelineError("NO_FILE", "yt-dlp produced no output")

    job.downloaded_file = os.path.join(temp_dir, files[0])
    job.transition_to(PipelineState.EXTRACTING)


# -------------------------------------------------
# 5. EXTRACTING
# -------------------------------------------------

def handle_extracting(job: Job):
    job.emit("Converting audio to MP3 (320kbps)")

    base, _ = os.path.splitext(job.downloaded_file)
    output_path = base + ".mp3"

    subprocess.run(
        ["ffmpeg", "-y", "-i", job.downloaded_file, "-ab", "320k", output_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    job.extracted_file = output_path
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
    results = search_itunes(hint.title, ", ".join(hint.artists))

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

    ensure_dir(LIBRARY_ROOT)

    title = safe_filename(job.final_metadata["trackName"])
    artist = safe_filename(job.final_metadata["artistName"])
    final_path = os.path.join(LIBRARY_ROOT, f"{title} - {artist}.mp3")

    if os.path.exists(final_path):
        job.result.path = final_path
        raise PipelineError("FILE_EXISTS", "Track already exists in library")

    shutil.move(job.extracted_file, final_path)

    job.result.success = True
    job.result.title = title
    job.result.artist = artist
    job.result.album = job.final_metadata.get("collectionName")
    job.result.source = "iTunes (verified)"
    job.result.path = final_path

    job.transition_to(PipelineState.FINALIZED)


# -------------------------------------------------
# 10. ARCHIVING
# -------------------------------------------------

def handle_archiving(job: Job):
    job.emit("No reliable metadata found — archiving track")

    archive_dir = os.path.join(LIBRARY_ROOT, "_Unidentified")
    ensure_dir(archive_dir)

    hint = job.identity_hint
    title = safe_filename(hint.title)
    artist = safe_filename(hint.artists[0] if hint.artists else "Unknown")

    final_path = os.path.join(archive_dir, f"{title} - {artist}.mp3")
    shutil.move(job.extracted_file, final_path)

    job.result.archived = True
    job.result.title = hint.title
    job.result.artist = ", ".join(hint.artists)
    job.result.reason = "Unverified metadata"
    job.result.path = final_path

    job.transition_to(PipelineState.FINALIZED)
