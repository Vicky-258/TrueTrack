# ==============================================================================
# TrueTrack Runtime Launcher (Windows)
# ==============================================================================

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------------
# Resolve script directory and switch to it
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Resolve script directory and switch to it (handles symlinks)
# ----------------------------------------------------------------------
$CurrentPath = $MyInvocation.MyCommand.Path
$Item = Get-Item -LiteralPath $CurrentPath

# Resolve symlinks if any
while ($Item.LinkType -eq 'SymbolicLink') {
    $Target = $Item.Target
    
    # Handle relative targets
    if (-not [System.IO.Path]::IsPathRooted($Target)) {
        $Target = Join-Path (Split-Path -Parent $Item.FullName) $Target
    }
    
    $CurrentPath = (Get-Item -LiteralPath $Target).FullName
    $Item = Get-Item -LiteralPath $CurrentPath
}

$ScriptDir = Split-Path -Parent $CurrentPath
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
