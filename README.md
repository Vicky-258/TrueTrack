# 🎵 TrueTrack

**TrueTrack** is a self-hosted, local-first music ingestion pipeline that turns vague track queries into **properly tagged, organized audio files** — with human-in-the-loop correction when needed.

It runs as a **local service** (API + background worker + web UI), designed to be:

* **Portable**: Runs entirely on your machine.
* **Resilient**: Works reliably even on restricted or unstable networks.
* **Transparent**: No cloud black boxes.

> Think: *“A local music brain that puts you in control.”*

---

## ✨ Features

* 🔍 **Fuzzy Track Resolution**: Handles ambiguous queries and asks for help when needed.
* 🧠 **Human-in-the-Loop**: You decide the correct intent and metadata.
* ⚙️ **Stateful & Resumable**: Jobs persist across restarts and crashes.
* 🎧 **High-Quality Storage**: Normalized metadata, deduplication, and deterministic organization.
* 🖥️ **Modern Web UI**: Track progress, resolve conflicts, and manage your library.
* 🧩 **Local-First**: No external cloud accounts required.

---

## 🚀 Quick Start

### 1. Prerequisites

* **Git** installed.
* **Internet Connection** (for initial install & metadata resolution).
* **Linux, macOS, or Windows**.

### 2. Installation

TrueTrack comes with automated installers that ensure you have everything you need (Python, Node.js, etc.).

#### 🐧 Linux / 🍎 macOS

Open your terminal and run:

```bash
curl -fsSL https://vicky-258.github.io/TrueTrack-Bootstrap/install.sh | bash
```

#### 🪟 Windows

Open PowerShell as Administrator and run:

```powershell
iwr -useb https://vicky-258.github.io/TrueTrack-Bootstrap/install.ps1 | iex
```

The installer will:

1. Check your system dependencies.
2. Install Python, Node.js, and other tools if missing.
3. Configure your environment (`.env`).
4. Build the project.
5. Offer to create a **Desktop Launcher** and **Global Command** (`truetrack`).

## 🪟 Windows Support Status

TrueTrack runs on Windows, and the installer (`install.ps1`) sets up the required environment (Python, Node.js, `uv`, etc.).

The core application works reliably when started manually. However, the PowerShell automation wrappers (`install.ps1`, `run.ps1`, global command setup) are still being refined and may occasionally require manual intervention.

If automated startup fails:

1. Open PowerShell.
2. Navigate to the TrueTrack project directory (the folder containing `app.py`, `worker/`, `frontend/`, etc.).
3. Start components manually:

   ```powershell
   # Backend
   .\.venv\Scripts\python.exe app.py

   # Worker (in another terminal)
   .\.venv\Scripts\python.exe worker\main.py

   # Frontend (if built by installer)
   node frontend\.next\standalone\server.js
   ```

For diagnostics:

```powershell
truetrack doctor
```

Logs are located at:

```
%LOCALAPPDATA%\TrueTrack\logs
```

Linux and macOS are currently the primary tested platforms.

If you encounter issues on Windows:

* Please open an issue: [https://github.com/vicky-258/TrueTrack/issues](https://github.com/vicky-258/TrueTrack/issues)
* Contributions to improve the PowerShell tooling are welcome.

---

## ▶️ Usage

Once installed, usage is managed via the `truetrack` command (or `run.sh`/`run.ps1` if running manually).

### 1. Global Command (Recommended)

Open any terminal and use the following commands:

* **Start** (Default):
  ```bash
  truetrack
  # OR
  truetrack start
  ```
  Launches the Backend, Worker, and Frontend in the background.

* **Stop**:
  ```bash
  truetrack stop
  ```
  Gracefully stops all running components.

* **Status**:
  ```bash
  truetrack status
  ```
  Shows running processes and the Web UI URL.

* **Doctor**:
  ```bash
  truetrack doctor
  ```
  Checks system health and dependencies. Can also fix issues (e.g., `truetrack doctor --fix yt-dlp`).

### 2. Desktop Launcher

Double-click the **TrueTrack** icon on your Desktop.
* This is equivalent to running `truetrack start`.
* To stop the application later, run `truetrack stop` in a terminal.

### 3. Manual Start

If you are running from source without the global alias:

**Unix/macOS:**
```bash
./run.sh [start|stop|status|doctor]
```

**Windows:**
```powershell
.\run.ps1 [start|stop|status|doctor]
```

The app runs at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (default)

---

## 🔒 Configuration Invariant

TrueTrack stores all job state and application settings at the path defined by `TRUETRACK_DB_PATH`.
This environment variable is **REQUIRED**. If unset, the application will fail to start.

The installers (`install_unix.sh` and `install_windows.ps1`) automatically configure this for you.
If running manually, ensure you load the `.env` file or export the variable before starting the application.

---

## ⚙️ Configuration

TrueTrack uses a `.env` file for **bootstrap configuration** (server settings and database location). The installer generates this for you.

**Key Settings:**

| Variable             | Description                                          |
| -------------------- | ---------------------------------------------------- |
| `TRUETRACK_DB_PATH`  | **REQUIRED** — Absolute path to the SQLite database. |
| `TRUETRACK_PORT`     | Port for the Web UI and API (default: `8000`).       |
| `TRUETRACK_HOST`     | Network address to bind to (default: `127.0.0.1`).   |
| `ALLOWED_ORIGINS`    | CORS allowed origins for the API.                    |
| `MUSIC_LIBRARY_ROOT` | **OPTIONAL** — Fallback path if not set in the app.  |

> **Note:** The Music Library location is managed within the application and persisted in the database. You do not need to edit `.env` to change it.

---

## 🧠 Architecture

TrueTrack is composed of three cooperating local parts:

```
┌────────────┐
│  Frontend  │  (Next.js Web UI)
└─────▲──────┘
      │ HTTP
┌─────┴──────┐
│    API     │  (FastAPI Server)
│ job control│
└─────▲──────┘
      │ Shared Database (SQLite)
┌─────┴──────┐
│   Worker   │  (Background Pipeline)
│ pipeline   │
└────────────┘
```

* **API**: Manages job state and control flow (never executes heavy tasks).
* **Worker**: Executes pipeline steps (downloading, tagging, moving) one by one.
* **Frontend**: Provides the user interface for monitoring and control.

---

## 🧩 What “Resilient” Means

In practice, resilience in TrueTrack means:

* Jobs survive crashes, restarts, and power loss.
* Once metadata is resolved, the pipeline can continue offline.
* No dependency on accounts, tokens, or always-on cloud services.
* Partial progress is never lost — work resumes from the last known safe state.

---

## 🚫 Non-Goals

TrueTrack is intentionally **not**:

* A streaming service
* A recommendation engine
* A cloud-synced or account-based music platform
* A DRM circumvention or piracy tool

Its focus is strictly on **local library ingestion, organization, and control**.

---

## 📂 Project Structure

```
truetrack/
├── install/              # Installer scripts
│   ├── install_unix.sh
│   ├── install_windows.ps1
│   └── common/           # Shared installer logic & assets
├── assets/               # Static assets (icons)
├── api/                  # Backend API (FastAPI)
├── core/                 # Pipeline logic & state machine
├── worker/               # Background worker runtime
├── infra/                # Database & persistence
├── frontend/             # Web UI (Next.js)
├── run.sh / .ps1         # Runtime wrappers
└── .env                  # Configuration file
```

---

## ❓ Troubleshooting

**"Dependencies missing"**
Run `truetrack doctor` to identify missing tools.
Run the installer again or use `truetrack doctor --fix yt-dlp` if specific tools are outdated.

**"Port already in use"**
Edit your `.env` file and change `TRUETRACK_PORT` (e.g., to `9000`), then restart.

**"Browser didn't open"**
Manually visit the URL printed in the terminal (usually `http://127.0.0.1:8000`).

---

## 📜 License

MIT License.

TrueTrack is designed for **local, personal library management**. Users are responsible for ensuring their usage complies with applicable local laws and content licenses.