#!/usr/bin/env bash
# ==============================================================================
# TrueTrack Runtime Launcher (Unix)
# ==============================================================================

set -e

# ----------------------------------------------------------------------
# Resolve absolute path and switch to it
# ----------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ----------------------------------------------------------------------
# Verify virtual environment
# ----------------------------------------------------------------------
if [[ ! -d ".venv" ]]; then
    echo "Error: Virtual environment not found in $SCRIPT_DIR"
    exit 1
fi

# Activate virtual environment
source ".venv/bin/activate"

# ----------------------------------------------------------------------
# Load .env into process environment (best-effort)
# ----------------------------------------------------------------------
if [[ -f ".env" ]]; then
    set -a
    source ".env"
    set +a
fi

# ----------------------------------------------------------------------
# Resolve host and port
# ----------------------------------------------------------------------
HOST="${TRUETRACK_HOST:-127.0.0.1}"
PORT="${TRUETRACK_PORT:-8000}"
URL="http://$HOST:$PORT"

# ----------------------------------------------------------------------
# Launch browser in background (non-blocking)
# ----------------------------------------------------------------------
(
    sleep 2

    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then
        open "$URL" >/dev/null 2>&1 || true
    else
        echo "Please open $URL in your browser."
    fi
) &

# ----------------------------------------------------------------------
# Start application server
# ----------------------------------------------------------------------
exec python3 app.py "$@"
