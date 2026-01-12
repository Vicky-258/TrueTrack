from typing import Callable, Dict
import requests
import subprocess
import json
import os
import shutil

from ytmusicapi import YTMusic
from core.job import IdentityHint
from core.states import PipelineState

from core.states import PipelineState
from core.job import Job
from core.scoring import score_metadata

from utils.paths import ensure_job_temp_dir
from utils.metadata import search_itunes
from utils.storage import ensure_dir, safe_filename, LIBRARY_ROOT
from utils.tagging import fetch_album_art
from utils.logging import step

from mutagen.id3 import (
    ID3,
    TIT2, TPE1, TALB, TPE2,
    TRCK, TDRC, APIC,
)
from mutagen.mp3 import MP3


# =========================
# Errors
# =========================

class PipelineError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# =========================
# Pipeline Core
# =========================

class Pipeline:
    def __init__(self, renderer=None):
        self.handlers: Dict[PipelineState, Callable[[Job], None]] = {}
        self.renderer = renderer   # ✅ DEFINED HERE

    def register(self, state: PipelineState, handler: Callable[[Job], None]):
        self.handlers[state] = handler

    def run(self, job: Job):
        
        def flush_message():
            if self.renderer and job.last_message:
                self.renderer.info(job.last_message)
                job.last_message = None
        try:
            while True:
                state = job.current_state
    
                if state in (PipelineState.FINALIZED, PipelineState.FAILED):
                    flush_message()
                    break
    
                handler = self.handlers.get(state)
                if not handler:
                    raise PipelineError(
                        "NO_HANDLER",
                        f"No handler registered for state {state.name}"
                    )
    
                prev = job.current_state
                
                if state == PipelineState.USER_INTENT_SELECTION:
                    if not self.renderer:
                        raise PipelineError("NO_RENDERER", "Intent selection requires renderer")
                
                    idx = self.renderer.request_intent_selection(
                        job.identity_candidates
                    )
                
                    if idx is None:
                        job.fail("USER_ABORT", "User cancelled intent selection")
                        break
                
                    chosen = job.identity_candidates[idx]
                
                    job.identity_hint = IdentityHint(
                        title=chosen.get("title"),
                        artists=[a["name"] for a in chosen.get("artists", [])],
                        album=chosen.get("album", {}).get("name"),
                        duration_ms=chosen.get("duration_seconds", 0) * 1000 if chosen.get("duration_seconds") else None,
                        video_id=chosen.get("videoId"),
                        uploader=chosen.get("artists", [{}])[0].get("name"),
                        confidence=100,   # user = truth
                    )
                
                    job.transition_to(PipelineState.SEARCHING)
                    self.renderer.on_state_change(job.current_state)
                    continue
    
                # 🔥 SPECIAL CASE: USER_SELECTION
                if state == PipelineState.USER_INTENT_SELECTION:
                    if not self.renderer:
                        raise PipelineError(
                            "NO_RENDERER",
                            "User selection required but no renderer available"
                        )
    
                    choice = self.renderer.request_user_selection(
                        job.metadata_candidates
                    )
    
                    # Cancel
                    if choice is None:
                        job.fail("USER_ABORT", "User cancelled selection")
                        break
    
                    selected = job.metadata_candidates[choice]
                    job.final_metadata = selected
                    job.metadata_confidence = 100  # user = ground truth
                    job.transition_to(PipelineState.TAGGING)
                    
                    if self.renderer:
                        self.renderer.on_state_change(job.current_state)
                    
                    flush_message()
                    continue
    
                # 🧠 NORMAL HANDLER FLOW
                handler(job)
    
                if job.current_state == prev:
                    raise PipelineError(
                        "NO_STATE_CHANGE",
                        f"Handler for {prev.name} did not advance state"
                    )
    
                if self.renderer:
                    self.renderer.on_state_change(job.current_state)
                
                flush_message()
    
        except PipelineError as e:
            job.fail(e.code, e.message)
            job.result.error = e.message

# =========================
# Handlers
# =========================

def handle_init(job: Job):
    job.transition_to(PipelineState.RESOLVING_IDENTITY)


# -------------------------------------------------
# 1. RESOLVING_IDENTITY (YTMusic heuristic)
# -------------------------------------------------

def handle_resolving_identity(job: Job):
    ytmusic = YTMusic()

    try:
        results = ytmusic.search(job.raw_query, filter="songs")
    except Exception as e:
        raise PipelineError("YTMUSIC_ERROR", f"Search failed: {e}")

    if not results:
        raise PipelineError("NO_IDENTITY", "YTMusic returned no results")

    # Limit for UX + determinism
    candidates = results[:5]
    job.identity_candidates = candidates

    # -----------------------------
    # Ambiguity heuristic (simple)
    # -----------------------------
    def is_ambiguous(candidates, query: str) -> bool:
        if len(candidates) <= 1:
            return False

        query_lower = query.lower()

        # If artist name not mentioned in query → ambiguity risk
        top_artists = [
            a["name"].lower()
            for a in candidates[0].get("artists", [])
        ]

        artist_in_query = any(a in query_lower for a in top_artists)

        return not artist_in_query

    # --------------------------------
    # EARLY INTENT SELECTION
    # --------------------------------
    if job.options.ask or is_ambiguous(candidates, job.raw_query):
        job.transition_to(PipelineState.USER_INTENT_SELECTION)
        return

    # --------------------------------
    # AUTO-PICK TOP RESULT
    # --------------------------------
    top = candidates[0]

    job.identity_hint = IdentityHint(
        title=top.get("title"),
        artists=[a["name"] for a in top.get("artists", [])],
        album=top.get("album", {}).get("name"),
        duration_ms=(
            top.get("duration_seconds", 0) * 1000
            if top.get("duration_seconds")
            else None
        ),
        video_id=top.get("videoId"),
        uploader=top.get("artists", [{}])[0].get("name"),
        confidence=80,  # heuristic confidence
    )

    # IMPORTANT: downstream stages rely ONLY on identity_hint
    job.transition_to(PipelineState.SEARCHING)

# -------------------------------------------------
# 2. SEARCHING_MEDIA (deterministic yt-dlp target)
# -------------------------------------------------

def handle_searching(job: Job):
    if not job.identity_hint:
        raise PipelineError(
            "NO_IDENTITY_HINT",
            "SEARCHING reached without resolved identity"
        )

    job.selected_source = {
        "url": f"https://www.youtube.com/watch?v={job.identity_hint.video_id}",
        "title": job.identity_hint.title,
        "duration": (job.identity_hint.duration_ms or 0) // 1000,
        "uploader": job.identity_hint.uploader,
    }
    job.source_candidates = [job.selected_source]
    job.transition_to(PipelineState.DOWNLOADING)

# -------------------------------------------------
# 3. DOWNLOADING
# -------------------------------------------------

def handle_downloading(job: Job):
    
    if job.options.dry_run:
        job.emit("Dry run enabled — skipping download")
        job.transition_to(PipelineState.FINALIZED)
        job.result.success = True
        job.result.title = job.identity_hint.title if job.identity_hint else job.query
        job.result.artist = "Unknown"
        job.result.source = "dry-run"
        job.result.path = "(not written)"
        return

    job.emit(f"Downloading audio: {job.selected_source['title']}")

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

    stdout = None
    stderr = None
    
    if not job.options.verbose:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
    
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.CalledProcessError:
        raise PipelineError("DOWNLOAD_FAILED", "yt-dlp failed to download audio")

    files = os.listdir(temp_dir)
    if not files:
        raise PipelineError("NO_FILE", "yt-dlp produced no output")

    if len(files) > 1:
        raise PipelineError("MULTIPLE_FILES", "Unexpected multiple files")

    job.downloaded_file = os.path.join(temp_dir, files[0])
    job.transition_to(PipelineState.EXTRACTING)


# -------------------------------------------------
# 4. EXTRACTING
# -------------------------------------------------

def handle_extracting(job: Job):
    job.emit(f"Processing audio: {os.path.basename(job.downloaded_file)}")

    input_path = job.downloaded_file
    temp_dir = job.temp_dir

    base, _ = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(temp_dir, f"{base}.mp3")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-ab", "320k",
        output_path,
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        raise PipelineError("FFMPEG_FAILED", "Audio extraction failed")

    if not os.path.exists(output_path):
        raise PipelineError("NO_OUTPUT_FILE", "ffmpeg produced no output")

    job.extracted_file = output_path
    job.transition_to(PipelineState.MATCHING_METADATA)


# -------------------------------------------------
# 5. MATCHING_METADATA (iTunes canonical)
# -------------------------------------------------

def handle_matching_metadata(job: Job):
    hint = job.identity_hint
    if not hint:
        raise PipelineError("NO_IDENTITY_HINT", "Missing identity hint")
        
    if job.options.force_archive:
        job.emit("Metadata matching skipped (force archive)")
        job.transition_to(PipelineState.ARCHIVING)
        return

    # ✅ identity comes from YTMusic
    title = hint.title
    artist = ", ".join(hint.artists)
    duration = (hint.duration_ms or 0) // 1000

    try:
        results = search_itunes(title, artist)
    except requests.RequestException as e:
        job.emit("iTunes search failed, falling back to archive")
        job.transition_to(PipelineState.ARCHIVING)
        return

    if not results:
        job.transition_to(PipelineState.ARCHIVING)
        return

    scored = []
    for r in results:
        score, reasons = score_metadata(
            r,
            title,
            artist,
            duration,
        )
        r["_score"] = score
        r["_reasons"] = reasons
        scored.append(r)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    best = scored[0]

    job.metadata_candidates = scored
    job.final_metadata = best
    job.metadata_confidence = best["_score"]
    
    if best["_score"] < 60:
        job.transition_to(PipelineState.USER_METADATA_SELECTION)
    
    job.transition_to(PipelineState.TAGGING)

# -------------------------------------------------
# 6. TAGGING
# -------------------------------------------------

def handle_tagging(job: Job):
    meta = job.final_metadata
    audio_path = job.extracted_file

    audio = MP3(audio_path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=meta["trackName"]))
    audio.tags.add(TPE1(encoding=3, text=meta["artistName"]))
    audio.tags.add(TPE2(encoding=3, text=meta["artistName"]))
    audio.tags.add(TALB(encoding=3, text=meta["collectionName"]))

    if meta.get("trackNumber"):
        audio.tags.add(TRCK(encoding=3, text=str(meta["trackNumber"])))

    if meta.get("releaseDate"):
        year = meta["releaseDate"].split("-")[0]
        audio.tags.add(TDRC(encoding=3, text=year))

    try:
        art = fetch_album_art(meta)
        if art:
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=art,
                )
            )
    except requests.RequestException as e:
        job.emit("Could not fetch album art")

    audio.save()
    job.transition_to(PipelineState.STORING)


# -------------------------------------------------
# 7. STORING
# -------------------------------------------------

def handle_storage(job: Job):
    if not job.extracted_file:
        raise PipelineError("NO_AUDIO", "No audio file to store")

    if not job.final_metadata:
        raise PipelineError("NO_METADATA", "No metadata for storage")

    meta = job.final_metadata

    # flat library root
    ensure_dir(LIBRARY_ROOT)

    title = safe_filename(meta["trackName"])
    artist = safe_filename(meta["artistName"])

    filename = f"{title} - {artist}.mp3"
    final_path = os.path.join(LIBRARY_ROOT, filename)

    if os.path.exists(final_path):
        raise PipelineError(
            "FILE_EXISTS",
            f"Track already exists: {final_path}"
        )

    shutil.move(job.extracted_file, final_path)

    job.final_path = final_path
    
    job.result.success = True
    job.result.title = meta["trackName"]
    job.result.artist = meta["artistName"]
    job.result.album = meta.get("collectionName")
    job.result.source = "iTunes (verified)"
    job.result.path = final_path
    
    job.transition_to(PipelineState.FINALIZED)

def handle_metadata_user_selection(job: Job):
    """
    Blocking state.
    User choice is handled by Pipeline + Renderer.
    """
    return

def handle_archiving(job: Job):
    step("ARCHIVING", "No reliable iTunes metadata")

    if not job.extracted_file:
        raise PipelineError("NO_AUDIO", "No extracted file to archive")

    if not job.identity_hint:
        raise PipelineError("NO_IDENTITY_HINT", "Cannot archive without identity hint")

    hint = job.identity_hint

    # -------- Tag using identity hint only --------
    audio = MP3(job.extracted_file, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    title = hint.title
    artists = ", ".join(hint.artists) if hint.artists else "Unknown Artist"
    album = hint.album or "Unknown Album"

    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artists))
    audio.tags.add(TPE2(encoding=3, text=hint.artists[0] if hint.artists else artists))
    audio.tags.add(TALB(encoding=3, text=album))

    audio.save()

    # -------- Store in _Unidentified --------
    archive_dir = os.path.join(LIBRARY_ROOT, "_Unidentified")
    ensure_dir(archive_dir)

    safe_title = safe_filename(title)
    safe_artist = safe_filename(hint.artists[0]) if hint.artists else "Unknown"

    filename = f"{safe_title} - {safe_artist}.mp3"
    final_path = os.path.join(archive_dir, filename)

    if os.path.exists(final_path):
        raise PipelineError("FILE_EXISTS", final_path)

    shutil.move(job.extracted_file, final_path)

    job.final_path = final_path
    job.metadata_confidence = 0
    
    job.result.archived = True
    job.result.title = title
    job.result.artist = artists
    job.result.album = album
    job.result.reason = "No reliable iTunes metadata"
    job.result.path = final_path

    job.transition_to(PipelineState.FINALIZED)

def run(self, job: Job, renderer=None):
    ...

def handle_user_intent_selection(job: Job):
    # Blocking state.
    # Actual user choice is handled by Pipeline.run + renderer.
    return
