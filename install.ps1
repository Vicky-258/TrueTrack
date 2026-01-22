$ErrorActionPreference = "Stop"

$InstallDir = "$env:USERPROFILE\.truetrack"
$RepoUrl = "https://github.com/Vicky-258/TrueTrack.git"

Write-Host "🎵 Installing TrueTrack..."

# -----------------------------
# Check git
# -----------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "Git is required. Install Git for Windows first."
}

# -----------------------------
# Install uv
# -----------------------------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "⬇️ Installing uv..."
  irm https://astral.sh/uv/install.ps1 | iex
}

# -----------------------------
# Clone / update
# -----------------------------
if (Test-Path $InstallDir) {
  Write-Host "🔄 Updating TrueTrack..."
  Set-Location $InstallDir
  git pull
} else {
  Write-Host "⬇️ Downloading TrueTrack..."
  git clone $RepoUrl $InstallDir
  Set-Location $InstallDir
}

.\install_core.ps1

Write-Host ""
Write-Host "✅ TrueTrack installed!"
Write-Host "👉 Run with: $InstallDir\run.ps1"
