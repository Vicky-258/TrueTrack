#!/bin/bash
set -e

# Resolve absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
    echo "Error: Virtual environment not found in $SCRIPT_DIR"
    exit 1
fi

source .venv/bin/activate

# Load .env if present
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

HOSTNAME="${TRUETRACK_HOST:-127.0.0.1}"
PORT="${TRUETRACK_PORT:-8000}"
URL="http://$HOSTNAME:$PORT"

# Open browser in background
(
    sleep 2
    if command -v xdg-open &> /dev/null; then
        xdg-open "$URL"
    elif command -v open &> /dev/null; then
        open "$URL"
    else
        echo "Please open $URL in your browser."
    fi
) &

# Execute server
exec python3 app.py "$@"
