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

---

## 🚧 Windows Installer Status (Please Read)

> **Short version:**
> The Windows installer is **functional but not yet fully hardened**. Some edge cases remain, and active maintenance is temporarily paused.

### What’s the situation?

The Windows installer (`install.ps1`) handles significant platform complexity, including:

* PowerShell 5.1 vs PowerShell 7 differences
* Execution policy and elevation behavior
* Python and Node.js bootstrapping
* Environment variable and PATH persistence

While the **core TrueTrack application is complete and stable**, there are **known rough edges** in the Windows installer on certain systems.

These issues are **installer-only** and do **not** reflect architectural problems with TrueTrack itself.

### Current State

* ✅ **Linux / macOS installers**: Stable and reliable
* ⚠️ **Windows installer**:

  * Works on many systems
  * Fails or behaves inconsistently on some setups
  * Needs further hardening and edge-case handling

### Why this isn’t fixed yet

This project is currently **paused**, not abandoned.

The Windows installer requires a careful, focused pass to be robust across environments. Rather than shipping rushed fixes or masking failures, the current state is documented transparently.

### What you can do

You have a few options:

#### 🕒 Wait

If you just want to *use* TrueTrack:

* Feel free to star the repository
* Check back later for a hardened Windows installer update

#### 🧠 Help Debug

If you’re comfortable with PowerShell:

* Run the installer manually
* Capture error output or logs
* Open an issue including:

  * Windows version
  * PowerShell version
  * Exact failure point

#### 🔧 Contribute a Fix

If you want to contribute directly:

* Focus area: `install/install_windows.ps1`
* Improvement goals:

  * Consistent behavior across PS 5.1 / 7
  * Better error detection and messaging
  * Reduced reliance on global system state

Pull requests and partial improvements are welcome.

### Manual Workaround (Advanced Users)

If the installer fails, you can still run TrueTrack manually by:

1. Installing Python and Node.js yourself
2. Cloning the repository
3. Setting `TRUETRACK_DB_PATH`
4. Starting the app using `run.ps1`

This is **not recommended for casual users**, but it does work.

---

## ▶️ Usage

Once installed, you can start TrueTrack in three ways:

### 1. Desktop Launcher (Recommended)

Double-click the **TrueTrack** icon on your Desktop (if you accepted the option during install).

* This starts the server and opens your browser automatically.
* To stop, simply close the terminal window that opens.

### 2. Global Command

Open any terminal and type:

```bash
truetrack
```

### 3. Manual Start

If you prefer the manual route:

**Unix/macOS:**

```bash
cd ~/.truetrack
./run.sh
```

**Windows:**

```powershell
cd $env:LOCALAPPDATA\TrueTrack
.\run.ps1
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
Run the installer again. It is idempotent and will fix missing tools.

**"Port already in use"**
Edit your `.env` file and change `TRUETRACK_PORT` (e.g., to `9000`), then restart.

**"Browser didn't open"**
Manually visit the URL printed in the terminal (usually `http://127.0.0.1:8000`).

---

## 📜 License

MIT License.

TrueTrack is designed for **local, personal library management**. Users are responsible for ensuring their usage complies with applicable local laws and content licenses.