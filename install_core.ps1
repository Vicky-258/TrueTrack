$ErrorActionPreference = "Stop"

Write-Host "🔧 Setting up dependencies..."

# -----------------------------
# Python check
# -----------------------------
$py = python --version 2>$null
if (-not $py) {
  Write-Error "Python is required (3.11+)"
}

# -----------------------------
# ffmpeg check
# -----------------------------
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Error "ffmpeg not found. Install ffmpeg and retry."
}

# -----------------------------
# Install deps
# -----------------------------
uv sync

Write-Host "🎉 Dependencies installed"
