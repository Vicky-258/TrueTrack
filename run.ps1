# ==============================================================================
# TrueTrack Runtime Launcher (Windows)
# ==============================================================================

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------------
# Resolve script directory and switch to it
# ----------------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ----------------------------------------------------------------------
# Verify virtual environment
# ----------------------------------------------------------------------
if (-not (Test-Path ".venv")) {
    Write-Error "Virtual environment not found in $ScriptDir"
    exit 1
}

# Activate virtual environment
. ".venv\Scripts\Activate.ps1"

# ----------------------------------------------------------------------
# Load .env into process environment (best-effort)
# ----------------------------------------------------------------------
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()

        # Skip empty lines and comments
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        # Parse KEY=VALUE
        if ($line -match "=") {
            $key, $value = $line.Split("=", 2)
            $key = $key.Trim()
            $value = $value.Trim().Trim('"')

            if ($key) {
                [Environment]::SetEnvironmentVariable(
                    $key,
                    $value,
                    "Process"
                )
            }
        }
    }
}

# ----------------------------------------------------------------------
# Resolve host and port
# ----------------------------------------------------------------------
$HostConf = $env:TRUETRACK_HOST
if (-not $HostConf) { $HostConf = "127.0.0.1" }

$PortConf = $env:TRUETRACK_PORT
if (-not $PortConf) { $PortConf = "8000" }

$Url = "http://$HostConf`:$PortConf"

# ----------------------------------------------------------------------
# Launch browser (non-blocking)
# ----------------------------------------------------------------------
Start-Process $Url -ErrorAction SilentlyContinue

# ----------------------------------------------------------------------
# Start application server
# ----------------------------------------------------------------------
python app.py @args
