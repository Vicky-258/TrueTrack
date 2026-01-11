from typing import Callable, Dict
from core.states import PipelineState
from core.job import Job
import json
from core.states import PipelineState
from core.job import Job
from core.scoring import score_candidate
import subprocess
import os
from utils.paths import ensure_job_temp_dir
from utils.metadata import search_itunes, score_metadata
from mutagen.id3 import (
    ID3,
    TIT2, TPE1, TALB, TPE2,
    TRCK, TDRC, APIC,
)
from mutagen.mp3 import MP3
from utils.storage import ensure_dir, safe_filename, LIBRARY_ROOT
import os
import shutil
from utils.tagging import fetch_album_art
from utils.logging import section, step, list_item


class PipelineError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class Pipeline:
    def __init__(self):
        self.handlers: Dict[PipelineState, Callable[[Job], None]] = {}

    def register(self, state: PipelineState, handler: Callable[[Job], None]):
        self.handlers[state] = handler

    def run(self, job: Job):
        try:
            while True:
                current = job.current_state
    
                if current in (PipelineState.FINALIZED, PipelineState.FAILED):
                    break
    
                handler = self.handlers.get(current)
                if handler is None:
                    raise PipelineError(
                        "NO_HANDLER",
                        f"No handler registered for state {current.name}"
                    )
    
                prev_state = job.current_state
                handler(job)
    
                if job.current_state == prev_state:
                    raise PipelineError(
                        "NO_STATE_CHANGE",
                        f"Handler for {prev_state.name} did not advance state"
                    )
    
        except PipelineError as e:
            job.fail(e.code, e.message)

def handle_init(job: Job):
    job.transition_to(PipelineState.SEARCHING)


def handle_searching(job: Job):
    query = job.normalized_query
    search_term = f"ytsearch5:{query}"

    cmd = [
        "yt-dlp",
        search_term,
        "--dump-json",
        "--no-playlist",
        "--quiet",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise PipelineError("SEARCH_FAILED", e.stderr.strip())

    candidates = []
    for line in result.stdout.splitlines():
        data = json.loads(line)

        candidates.append({
            "url": data.get("webpage_url"),
            "title": data.get("title"),
            "duration": data.get("duration"),
            "uploader": data.get("uploader"),
        })

    if not candidates:
        raise PipelineError("NO_RESULTS", "No search results found")
        
    artist_guess = job.raw_query.split("-")[-1].strip()
    
    scored = []
    for c in candidates:
        score, reasons = score_candidate(c, artist_guess)
        c["score"] = score
        c["score_reasons"] = reasons
        scored.append(c)
    
    # sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    job.source_candidates = scored
    job.selected_source = scored[0]
    
    print("\n📊 SCORING RESULTS")
    print("-" * 40)
    
    for i, c in enumerate(scored, start=1):
        print(f"{i}. {c['title']}")
        print(f"   score   : {c['score']}")
        print(f"   reasons : {c['score_reasons']}")
        print()
        
    job.transition_to(PipelineState.DOWNLOADING)

def handle_downloading(job):
    step("DOWNLOADING", job.selected_source["title"])
    if not job.selected_source:
        raise PipelineError("NO_SOURCE", "No source selected for download")

    url = job.selected_source["url"]

    temp_dir = ensure_job_temp_dir(job.job_id)
    job.temp_dir = temp_dir

    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        url,
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-quality", "0",
        "--output", output_template,
        "--quiet",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise PipelineError("DOWNLOAD_FAILED", str(e))

    # find downloaded file
    files = os.listdir(temp_dir)
    if not files:
        raise PipelineError("NO_FILE", "yt-dlp produced no output")

    if len(files) > 1:
        raise PipelineError("MULTIPLE_FILES", "Unexpected multiple downloaded files")

    job.downloaded_file = os.path.join(temp_dir, files[0])

    job.transition_to(PipelineState.EXTRACTING)
    
def handle_extracting(job):
    step("EXTRACTING", os.path.basename(job.downloaded_file))
    if not job.downloaded_file:
        raise PipelineError("NO_DOWNLOADED_FILE", "No file to extract")

    input_path = job.downloaded_file
    temp_dir = job.temp_dir

    if not os.path.exists(input_path):
        raise PipelineError("MISSING_INPUT_FILE", input_path)

    # derive output path
    base_name, _ = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(temp_dir, f"{base_name}.mp3")

    cmd = [
        "ffmpeg",
        "-y",                # overwrite if exists
        "-i", input_path,    # input file
        "-vn",               # no video
        "-ab", "320k",       # audio bitrate
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

    # IMPORTANT: advance state
    job.transition_to(PipelineState.MATCHING_METADATA)
    
def handle_matching_metadata(job):
    if not job.extracted_file:
        raise PipelineError("NO_AUDIO", "No extracted audio for metadata")

    # derive expectations
    raw = job.raw_query.split("-")
    expected_title = raw[0].strip()
    expected_artist = raw[1].strip() if len(raw) > 1 else ""

    duration = job.selected_source.get("duration", 0)

    results = search_itunes(expected_title, expected_artist)

    if not results:
        raise PipelineError("NO_METADATA", "No metadata candidates found")

    scored = []
    for r in results:
        score, reasons = score_metadata(
            r,
            expected_title,
            expected_artist,
            duration,
        )
        r["_score"] = score
        r["_reasons"] = reasons
        scored.append(r)

    scored.sort(key=lambda x: x["_score"], reverse=True)

    job.metadata_candidates = scored
    job.final_metadata = scored[0]
    job.metadata_confidence = scored[0]["_score"]

    if job.metadata_confidence < 60:
        raise PipelineError(
            "LOW_CONFIDENCE",
            f"Metadata confidence too low ({job.metadata_confidence})"
        )

    job.transition_to(PipelineState.TAGGING)
    
def handle_tagging(job):
    if not job.extracted_file:
        raise PipelineError("NO_AUDIO", "No extracted MP3 to tag")

    if not job.final_metadata:
        raise PipelineError("NO_METADATA", "No metadata available for tagging")

    audio_path = job.extracted_file
    meta = job.final_metadata

    # Load MP3 + ID3
    audio = MP3(audio_path, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    # Core tags
    audio.tags.add(TIT2(encoding=3, text=meta["trackName"]))
    audio.tags.add(TPE1(encoding=3, text=meta["artistName"]))       # Artist
    audio.tags.add(TPE2(encoding=3, text=meta["artistName"]))       # Album Artist
    audio.tags.add(TALB(encoding=3, text=meta["collectionName"]))   # Album

    # Track number
    track_no = meta.get("trackNumber")
    if track_no:
        audio.tags.add(TRCK(encoding=3, text=str(track_no)))

    # Year
    release_date = meta.get("releaseDate", "")
    if release_date:
        year = release_date.split("-")[0]
        audio.tags.add(TDRC(encoding=3, text=year))

    # Album art
    art_bytes = fetch_album_art(meta)
    if art_bytes:
        audio.tags.add(
            APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,  # front cover
                desc="Cover",
                data=art_bytes,
            )
        )

    audio.save()

    # advance pipeline
    job.transition_to(PipelineState.STORING)
    
def handle_storage(job):
    step("STORING", job.final_path)
    if not job.extracted_file:
        raise PipelineError("NO_AUDIO", "No audio file to store")

    if not job.final_metadata:
        raise PipelineError("NO_METADATA", "No metadata for storage")

    meta = job.final_metadata

    artist = safe_filename(meta["artistName"])
    album = safe_filename(meta["collectionName"])
    title = safe_filename(meta["trackName"])

    artist_dir = os.path.join(LIBRARY_ROOT, artist)
    album_dir = os.path.join(artist_dir, album)

    ensure_dir(album_dir)

    filename = f"{title} - {artist}.mp3"
    final_path = os.path.join(album_dir, filename)

    if os.path.exists(final_path):
        raise PipelineError(
            "FILE_EXISTS",
            f"Track already exists: {final_path}"
        )

    shutil.move(job.extracted_file, final_path)

    job.final_path = final_path
    job.transition_to(PipelineState.FINALIZED)

def inspect_candidates(job):
    print("\n" + "=" * 60)
    print("🔍 SEARCH INSPECTION")
    print("=" * 60)

    for idx, c in enumerate(job.source_candidates, start=1):
        title = c.get("title", "")
        uploader = c.get("uploader", "unknown")
        duration = c.get("duration", 0)

        t = title.lower()
        flags = []

        if "official" in t:
            flags.append("official")
        if "lyrics" in t:
            flags.append("lyrics")
        if "live" in t:
            flags.append("live")
        if "remaster" in t:
            flags.append("remaster")

        flag_str = ", ".join(flags) if flags else "none"

        print(f"{idx:>2}. {title}")
        print(f"    • uploader : {uploader}")
        print(f"    • duration : {duration}s")
        print(f"    • flags    : {flag_str}")
        print("-" * 60)

