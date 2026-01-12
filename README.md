# TrueTrack

A CLI-based backend pipeline for **resolving user intent, downloading audio, applying canonical metadata, and organizing a local music library**.

The system is designed to prioritize **correctness over blind automation** by resolving ambiguous song intent *before* download and only requesting user input when confidence is low.

---

## Features

* **Early Intent Resolution**
  Ambiguous queries trigger a user selection step *before download*, preventing silent misidentification.

* **High-Quality Audio Ingestion**
  Downloads best available audio streams via `yt-dlp` and converts them to high-quality MP3.

* **Canonical Metadata Matching**
  Fetches official metadata and album art from iTunes when confidence is sufficient.

* **Smart Tagging**
  Embeds ID3 tags including title, artist, album, year, and album art.

* **Resilient Fallbacks**
  Automatically archives tracks without metadata when canonical matching fails.

* **Headless Core Architecture**
  Clean separation between pipeline logic and CLI rendering, making the backend UI-ready.

---

## Prerequisites

Ensure the following are installed and available in your `PATH`:

* **Python 3.10+**
* **ffmpeg** (audio extraction)
* **yt-dlp** (media downloading)

---

## Installation

This project uses **`uv`** for dependency management (recommended), but standard `pip` is also supported.

### Option A: Using `uv` (Recommended)

```bash
uv sync
```

Run directly:

```bash
uv run python ingest.py "Song Name"
```

---

### Option B: Using `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Usage

The main entry point is `ingest.py`.

```bash
# Basic usage
python ingest.py "Everything - Alex Warren"

# Force early intent selection
python ingest.py "Everything" --ask

# Verbose output (show yt-dlp / ffmpeg logs)
python ingest.py "Blue" --verbose

# Dry run (no download or file writes)
python ingest.py "Halo" --dry-run
```

### Flags

* `--ask`
  Force **early intent selection** before download.

* `--verbose`
  Show logs from underlying tools (`yt-dlp`, `ffmpeg`).

* `--dry-run`
  Execute the pipeline without downloading or writing files.

* `--force-archive`
  Skip metadata matching and archive immediately.

---

## Configuration

By default, music is stored in:

```
~/Music/library
```

You can override this location using an environment variable:

```bash
export MUSIC_LIBRARY_ROOT="/path/to/your/music"
python ingest.py "Song Name"
```

---

## Legal Notice

This project is intended for **personal use and educational purposes**.

It does not host, distribute, or provide copyrighted content.
Users are responsible for ensuring they have the right to download and store any media accessed using this tool.

---

## Notes

* Intent selection occurs **before download** when queries are ambiguous.
* Metadata confirmation is requested **only when confidence is low**.
* Search results depend on YouTube Music availability and ranking.
* The project is non-commercial and provided as-is.

---

## Status

**Version:** v1 (stabilization complete)
Core architecture is stable; future versions may improve heuristics, UX polish, and automation.

---

Made with ❤️ by **Rouge Coders**

