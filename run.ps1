
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".venv")) {
    Write-Error "Virtual environment not found in $ScriptDir"
    exit 1
}

. ".venv\Scripts\Activate.ps1"

# Load .env manually since powershell doesn't 'source' it easily
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^[^#]*=") {
            $k,$v = $_.Split('=',2)
            [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim(), "Process")
        }
    }
}

$HostConf = $env:TRUETRACK_HOST
if (-not $HostConf) { $HostConf = "127.0.0.1" }
$PortConf = $env:TRUETRACK_PORT
if (-not $PortConf) { $PortConf = "8000" }

$Url = "http://$HostConf`:$PortConf"

# Start Browser
Start-Process $Url

# Execute server
python app.py $args
