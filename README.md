# TrueTrack

**TrueTrack** is a production-grade backend system for **resolving music intent, downloading audio, applying canonical metadata, and organizing a local music library**.

It is built around a **state-machine–driven pipeline** and a **background worker architecture**, prioritizing **correctness, observability, and resilience** over blind automation.

The system resolves ambiguous intent *before* committing to downloads and only requests user input when confidence is insufficient.

---

## Core Concepts

TrueTrack is designed around three principles:

1. **Intent before action**
   Ambiguous queries are resolved *before* download to prevent silent misidentification.

2. **Deterministic pipelines**
   Each job advances one explicit state at a time, making progress observable, debuggable, and restart-safe.

3. **Resilient execution**
   Failures are isolated, retried with backoff when appropriate, and never block the API.

---

## Architecture Overview (v2)

TrueTrack is split into three independent layers:

```
api/        → HTTP interface (job creation, status, user input, cancellation)
worker/     → Background worker executing pipeline steps
core/       → Pure pipeline logic and state machine
```

### Key Properties

* **API-first** (non-blocking, asynchronous)
* **Background workers** (step-based execution)
* **Persistent jobs** (SQLite)
* **Locking + retries** (safe under crashes)
* **Pause/resume via USER_* states**
* **Idempotent job creation**
* **Cancellation support**

---

## Features

### ✅ Intent Resolution

* Uses YouTube Music search to resolve candidate tracks
* Pauses for user input when confidence is low
* Prevents incorrect downloads caused by ambiguous queries

### ✅ High-Quality Audio Ingestion

* Downloads best available audio using `yt-dlp`
* Converts to high-quality MP3 via `ffmpeg`

### ✅ Canonical Metadata Matching

* Matches official metadata via iTunes
* Applies confidence scoring
* Requests user confirmation only when needed

### ✅ Smart Tagging

* Embeds ID3 tags (title, artist, album, year)
* Downloads and embeds album art when available

### ✅ Resilient Fallbacks

* Archives tracks when metadata cannot be confidently resolved
* Treats existing files as successful outcomes (no duplicate failures)

### ✅ Production-Grade Execution

* Background worker with job locking
* Retry with exponential backoff
* Safe crash recovery
* Explicit cancellation support

---

## Prerequisites

Ensure the following are installed and available in your `PATH`:

* **Python 3.10+**
* **ffmpeg** (audio conversion)
* **yt-dlp** (media downloading)

---

## Installation

This project uses **`uv`** for dependency management (recommended).

```bash
uv sync
```

---

## Running the System

### 1️⃣ Start the API

```bash
uv run uvicorn api.main:app --reload
```

### 2️⃣ Start the Worker

In a separate terminal:

```bash
uv run python -m worker.main
```

The worker will continuously process runnable jobs.

---

## API Usage

### Create a Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Numb Linkin Park",
    "options": { "ask": false }
  }'
```

Supports **idempotency** via header:

```http
Idempotency-Key: your-key-here
```

---

### Check Job Status

```bash
curl http://localhost:8000/jobs/<job_id>
```

Possible statuses:

* `running`
* `waiting` (USER_* input required)
* `success`
* `error`
* `cancelled`

---

### Provide User Input (Intent / Metadata)

```bash
curl -X POST http://localhost:8000/jobs/<job_id>/input \
  -H "Content-Type: application/json" \
  -d '{ "choice": 0 }'
```

---

### Cancel a Job

```bash
curl -X POST http://localhost:8000/jobs/<job_id>/cancel
```

Cancellation is terminal and idempotent.

---

## Configuration

By default, music is stored in:

```
~/Music/library
```

Override via environment variable:

```bash
export MUSIC_LIBRARY_ROOT="/path/to/music"
```

---

## Retry & Failure Semantics

* Transient worker errors are retried with backoff
* Deterministic pipeline errors fail immediately
* Existing files are treated as **successful outcomes**
* Cancelled jobs are never retried

---

## Legal Notice

This project is intended for **personal and educational use only**.

It does not host, distribute, or provide copyrighted content.
Users are responsible for ensuring they have the right to download and store any media accessed using this tool.

---

## Status

**Version:** **v2.0.0 (Locked)**

v2 is considered **stable and production-ready**.

### Guarantees

* API contract is frozen
* Pipeline semantics are stable
* Job persistence schema is stable

Future versions (v2.1+) may add:

* Expanded test coverage
* Authentication / access control
* Observability improvements
* Storage backends beyond SQLite

---

Made with ❤️ by **Rouge Coders**
*Truth over automation. Correctness over convenience.*


