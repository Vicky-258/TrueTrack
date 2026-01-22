# ==============================================================================
# Environment File Writer (Windows)
# ==============================================================================

function Write-EnvFile {
    param(
        [string]$SourceFile,
        [string]$TargetFile,
        [hashtable]$Updates
    )

    if (-not (Test-Path $SourceFile)) {
        Throw "Source env file not found: $SourceFile"
    }

    Write-Host "[INFO] Generating $TargetFile from $SourceFile..." -ForegroundColor Blue

    $lines = Get-Content $SourceFile
    $newLines = @()

    foreach ($line in $lines) {
        $matched = $false
        foreach ($key in $Updates.Keys) {
            # Check for "KEY=..." or "# KEY=..."
            # Regex: ^#?\s*KEY=
            if ($line -match "^#?\s*$key=") {
                $newLines += "$key=$($Updates[$key])"
                $matched = $true
                break
            }
        }
        
        if (-not $matched) {
            $newLines += $line
        }
    }

    # Check for keys that weren't in the source and append them? 
    # The logic above replaces found lines. 
    # If a key wasn't found, we should append it.
    
    foreach ($key in $Updates.Keys) {
        $alreadyPresent = $false
        foreach ($line in $lines) {
            if ($line -match "^#?\s*$key=") {
                $alreadyPresent = $true
                break
            }
        }
        if (-not $alreadyPresent) {
            $newLines += "$key=$($Updates[$key])"
        }
    }

    $newLines | Out-File -FilePath $TargetFile -Encoding utf8
    Write-Host "[SUCCESS] Environment configuration written." -ForegroundColor Green
}
