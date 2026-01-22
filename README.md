# 🎵 TrueTrack

**TrueTrack** is a self-hosted, local-first music ingestion pipeline that turns vague track queries into **properly tagged, organized audio files** — with human-in-the-loop correction when needed.

It runs as a **local service** (API + background worker + web UI), designed to be:

* portable
* debuggable
* respectful of user control
* resilient on restricted networks

> Think: *“a local music brain, not a cloud black box.”*

---

## ✨ Features

* 🔍 **Fuzzy track resolution**

  * Handles ambiguous queries
  * Pauses for user input when confidence is low
* 🧠 **Human-in-the-loop pipeline**

  * Intent selection
  * Metadata selection
  * Resume / cancel at any stage
* ⚙️ **Stateful job system**

  * Persistent job history
  * Resume after crashes or restarts
* 🎧 **Proper tagging & storage**

  * Normalized metadata
  * Deduplicated storage
* 🖥️ **Web UI**

  * Track job progress in real time
  * Interactive conflict resolution
* 🧩 **Local-first & self-hosted**

  * No cloud dependency
  * Runs entirely on your machine

---

## 🧠 Architecture Overview

TrueTrack is composed of **three cooperating parts**:

```
┌────────────┐
│  Frontend  │  (Next.js SPA)
└─────▲──────┘
      │ HTTP
┌─────┴──────┐
│    API     │  (FastAPI)
│ job control│
└─────▲──────┘
      │ shared store
┌─────┴──────┐
│   Worker   │  (background executor)
│ pipeline   │
└────────────┘
```

### Key design choices

* **API never executes jobs**
* **Worker executes exactly one pipeline step per tick**
* **All state is persisted**
* **Cancellation and resume are first-class**

This makes the system:

* crash-safe
* inspectable
* predictable

---

## 📦 Project Structure

```
truetrack/
├── app.py                # canonical entrypoint
├── api/                  # FastAPI routes & schemas
├── core/                 # pipeline logic & states
├── worker/               # background worker runtime
├── infra/                # persistence layer
├── frontend/             # web UI (Next.js)
├── utils/                # shared helpers
├── install.sh            # Unix installer
├── install.ps1           # Windows installer
├── run.sh                # Unix runner
├── run.ps1               # Windows runner
├── pyproject.toml        # Python deps
└── uv.lock               # locked environment
```

---

## ✅ System Requirements

TrueTrack intentionally keeps requirements minimal and explicit.

### Required

* **Python ≥ 3.11**
* **ffmpeg** available in `PATH`
* Internet access for:

  * YouTube / metadata APIs
  * initial install

### Supported Platforms

* Linux
* macOS
* Windows (PowerShell)

> No admin / sudo access required.

---

## 🚀 Installation

### Linux / macOS

```bash
curl -fsSL https://truetrack.sh/install.sh | sh
```

### Windows (PowerShell)

```powershell
iwr https://truetrack.sh/install.ps1 -useb | iex
```

The installer will:

1. Check system requirements
2. Install `uv` if missing
3. Download TrueTrack into `~/.truetrack`
4. Install dependencies

---

## ▶️ Running TrueTrack

### Linux / macOS

```bash
~/.truetrack/run.sh
```

### Windows

```powershell
$HOME\.truetrack\run.ps1
```

By default, the service starts on:

```
http://127.0.0.1:8000
```

Open this in your browser to access the UI.

---

## ⚙️ Configuration

TrueTrack is configured entirely via **environment variables**.

| Variable              | Default                 | Description       |
| --------------------- | ----------------------- | ----------------- |
| `TRUETRACK_HOST`      | `127.0.0.1`             | Bind address      |
| `TRUETRACK_PORT`      | `8000`                  | API/UI port       |
| `TRUETRACK_LOG_LEVEL` | `info`                  | Logging verbosity |
| `ALLOWED_ORIGINS`     | `http://localhost:3000` | CORS              |

You can override these before running:

```bash
export TRUETRACK_PORT=9000
./run.sh
```

---

## 🧪 Job Lifecycle

Each track request becomes a **job** that moves through explicit states:

```
RESOLVING_IDENTITY
→ USER_INTENT_SELECTION (optional)
→ SEARCHING
→ DOWNLOADING
→ EXTRACTING
→ MATCHING_METADATA
→ USER_METADATA_SELECTION (optional)
→ TAGGING
→ STORING
→ FINALIZED
```

### Control operations

* Cancel at any time
* Resume from safe checkpoints
* Inspect full state history

---

## 🔁 Resume & Fault Tolerance

TrueTrack is designed to survive:

* crashes
* restarts
* power loss
* user cancellation

All jobs are persisted in a local database and can be resumed safely.

---

## 🔐 Security Model

TrueTrack assumes a **trusted local environment**.

* No authentication by default
* Intended for localhost / LAN use
* For exposure beyond localhost:

  * use a reverse proxy
  * add authentication externally

---

## 🐳 Docker Support (Optional)

Docker support is **best-effort** and may not work on restricted networks.

TrueTrack does **not require Docker** and is intentionally designed to run without it.

---

## 🧹 Uninstall

TrueTrack is fully self-contained.

```bash
rm -rf ~/.truetrack
```

No system files are touched.

---

## 🗺️ Roadmap (Non-binding)

* `truetrack` CLI command
* Config file (`truetrack.toml`)
* Plugin system
* Optional auth
* CI-built Docker images

---

## 📜 Philosophy

TrueTrack prioritizes:

* **clarity over cleverness**
* **explicit state over hidden magic**
* **user control over automation**
* **portability over infrastructure hype**

---

## ❤️ A Note on Scope

TrueTrack is a **personal, self-hosted tool**.

It is not:

* a commercial service
* a DRM bypass tool
* a cloud scraper

Use responsibly.

---

## 🏁 Status

> **TrueTrack is feature-complete and stable for local use.**

Docker and packaging improvements may come later, but the core system is finished.
