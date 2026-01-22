# 🎵 TrueTrack

**TrueTrack** is a self-hosted, local-first music ingestion pipeline that turns vague track queries into **properly tagged, organized audio files** — with human-in-the-loop correction when needed.

It runs as a **local service** (API + background worker + web UI), designed to be:
* **Portable**: Runs entirely on your machine.
* **Resilient**: Works on restricted networks.
* **Transparent**: No cloud black boxes.

> Think: *“A local music brain that puts you in control.”*

---

## ✨ Features

* 🔍 **Fuzzy Track Resolution**: Handles ambiguous queries and asks for help when needed.
* 🧠 **Human-in-the-Loop**: You decide the correct intent and metadata.
* ⚙️ **Stateful & Resumable**: Jobs persist across restarts and crashes.
* 🎧 **High-Quality Storage**: Normalized metadata, deduplication, and proper organization.
* 🖥️ **Modern Web UI**: Track progress, resolve conflicts, and manage your library.
* 🧩 **Local-First**: No external cloud accounts required.

---

## 🚀 Quick Start

### 1. Prerequisites
* **Git** installed.
* **Internet Connection** (for initial install & metadata).
* **Linux, macOS, or Windows**.

### 2. Installation

TrueTrack comes with automated installers that ensure you have everything you need (Python, Node.js, etc.).

#### 🐧 Linux / 🍎 macOS
Open your terminal and run:

```bash
./install/install_unix.sh
```

#### 🪟 Windows
Open PowerShell as Administrator and run:

```powershell
.\install\install_windows.ps1
```

The installer will:
1. Check your system dependencies.
2. Install Python, Node.js, and other tools if missing.
3. Configure your environment (`.env`).
4. Build the project.
5. Offer to create a **Desktop Launcher** and **Global Command** (`truetrack`).

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

The app runs at: **http://127.0.0.1:8000** (default)

---

## ⚙️ Configuration

TrueTrack uses a `.env` file for configuration. The installer generates this for you, but you can customize it located in your install directory (`~/.truetrack` or `%LOCALAPPDATA%\TrueTrack`).

**Key Settings:**

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MUSIC_LIBRARY_ROOT` | `~/Music` | Where your music files are stored. |
| `TRUETRACK_PORT` | `8000` | Port for the Web UI and API. |
| `TRUETRACK_HOST` | `127.0.0.1` | Network address to bind to. |

To apply changes, restart TrueTrack.

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
* **Worker**: Executes the pipeline steps (downloading, tagging, moving) one by one.
* **Frontend**: Provides the user interface for monitoring and control.

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
Edit your `.env` file and change `TRUETRACK_PORT` to something else (e.g., 9000), then restart.

**"Browser didn't open"**
You can manually visit the URL printed in the terminal (usually `http://127.0.0.1:8000`).

---

## 📜 License

MIT License. Local, personal use is encouraged.
