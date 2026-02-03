#!/usr/bin/env bash
# ==============================================================================
# TrueTrack Runtime Launcher (Unix)
# ==============================================================================

set -e

# ----------------------------------------------------------------------
# Resolve absolute path and switch to it (handles symlinks)
# ----------------------------------------------------------------------
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$SCRIPT_DIR"

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
USER_DATA_DIR="$HOME/.truetrack"
PID_DIR="$USER_DATA_DIR/pids"
LOG_DIR="$USER_DATA_DIR/logs"

API_PID_FILE="$PID_DIR/api.pid"
WORKER_PID_FILE="$PID_DIR/worker.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

API_LOG="$LOG_DIR/api.log"
WORKER_LOG="$LOG_DIR/worker.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Default command
COMMAND="${1:-start}"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

check_pid() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    return 1
}

# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------

case "$COMMAND" in
    start)
        # 1. Verify Virtual Environment
        if [[ ! -d ".venv" ]]; then
            echo "Error: Virtual environment not found in $SCRIPT_DIR"
            exit 1
        fi
        source ".venv/bin/activate"

        # 2. Load .env (best-effort)
        if [[ -f ".env" ]]; then
            set -a
            source ".env"
            set +a
        fi

        # 3. Create Directories
        mkdir -p "$PID_DIR" "$LOG_DIR"

        # 4. Check if already running
        RUNNING=0
        if check_pid "$API_PID_FILE" >/dev/null; then echo "Backend already running ($(cat $API_PID_FILE))"; RUNNING=1; fi
        if check_pid "$WORKER_PID_FILE" >/dev/null; then echo "Worker already running ($(cat $WORKER_PID_FILE))"; RUNNING=1; fi
        if check_pid "$FRONTEND_PID_FILE" >/dev/null; then echo "Frontend already running ($(cat $FRONTEND_PID_FILE))"; RUNNING=1; fi
        
        if [ "$RUNNING" -eq 1 ]; then
            echo "TrueTrack is already running. Use '$0 stop' first if you want to restart."
            exit 1
        fi

        echo "Starting TrueTrack..."

        # 5. Launch Components
        export TRUETRACK_SKIP_FRONTEND=1
        
        # Backend
        nohup python3 app.py >> "$API_LOG" 2>&1 &
        echo $! > "$API_PID_FILE"
        echo "Started Backend (PID $(cat $API_PID_FILE))"

        # Worker
        nohup python3 worker/main.py >> "$WORKER_LOG" 2>&1 &
        echo $! > "$WORKER_PID_FILE"
        echo "Started Worker (PID $(cat $WORKER_PID_FILE))"

        # Frontend
        # Frontend path resolution logic from app.py
        FRONTEND_DIR="$SCRIPT_DIR/frontend"
        NEXT_SERVER="$FRONTEND_DIR/.next/standalone/server.js"
        if [ ! -f "$NEXT_SERVER" ]; then
            echo "Error: Next.js server not found at $NEXT_SERVER"
            echo "Did you run the installer?"
            # Cleanup launched processes
            kill $(cat "$API_PID_FILE") 2>/dev/null || true
            kill $(cat "$WORKER_PID_FILE") 2>/dev/null || true
            exit 1
        fi

        export HOSTNAME="${TRUETRACK_HOST:-127.0.0.1}"
        export PORT="${TRUETRACK_PORT:-3000}" 
        
        (cd "$FRONTEND_DIR" && PORT=3001 nohup node "$NEXT_SERVER" >> "$FRONTEND_LOG" 2>&1 & echo $! > "$FRONTEND_PID_FILE")
        echo "Started Frontend (PID $(cat $FRONTEND_PID_FILE))"

        echo "TrueTrack started."
        echo "Web UI: http://${TRUETRACK_HOST:-127.0.0.1}:${TRUETRACK_PORT:-8000}"
        echo "Web UI: http://${TRUETRACK_HOST:-127.0.0.1}:${TRUETRACK_PORT:-8000}"
        ;;

    doctor)
        # 1. Verify Virtual Environment
        if [[ ! -d ".venv" ]]; then
            echo "Error: Virtual environment not found in $SCRIPT_DIR"
            exit 1
        fi
        
        # 2. Load .env (best-effort)
        if [[ -f ".env" ]]; then
            set -a
            source ".env"
            set +a
        fi
        
        # 3. Run Doctor directly (foreground)
        "$SCRIPT_DIR/.venv/bin/python3" -m cli.doctor "${@:2}"
        ;;

    stop)
        echo "Stopping TrueTrack..."
        STOPPED=0
        
        stop_process() {
            local name=$1
            local pid_file=$2
            if pid=$(check_pid "$pid_file"); then
                echo "Stopping $name ($pid)..."
                kill "$pid" 2>/dev/null || true
                rm -f "$pid_file"
                STOPPED=1
            else
                [ -f "$pid_file" ] && rm -f "$pid_file" # Clean stale
            fi
        }

        stop_process "Backend" "$API_PID_FILE"
        stop_process "Worker" "$WORKER_PID_FILE"
        stop_process "Frontend" "$FRONTEND_PID_FILE"

        if [ "$STOPPED" -eq 1 ]; then
            echo "TrueTrack stopped."
        else
            echo "TrueTrack was not running."
        fi
        ;;

    status)
        RUNNING_COUNT=0
        
        check_component() {
            local name=$1
            local pid_file=$2
            if pid=$(check_pid "$pid_file"); then
                echo "$name: RUNNING (PID $pid)"
                RUNNING_COUNT=$((RUNNING_COUNT + 1))
            else
                echo "$name: STOPPED"
            fi
        }

        echo "TrueTrack Status:"
        echo "-----------------"
        check_component "Backend" "$API_PID_FILE"
        check_component "Worker" "$WORKER_PID_FILE"
        check_component "Frontend" "$FRONTEND_PID_FILE"
        echo "-----------------"
        
        if [ "$RUNNING_COUNT" -gt 0 ]; then
             # Source .env for host/port display
            if [[ -f ".env" ]]; then
                set -a
                source ".env"
                set +a
            fi
            echo "Web UI: http://${TRUETRACK_HOST:-127.0.0.1}:${TRUETRACK_PORT:-8000}"
        fi
        ;;

    help|--help|-h)
        echo "TrueTrack Manager"
        echo "-----------------"
        echo "Usage: $(basename "$0") [command]"
        echo ""
        echo "Commands:"
        echo "  start   Start TrueTrack (Backend, Worker, Frontend)"
        echo "  stop    Stop all TrueTrack processes"
        echo "  status  Show process status and Web UI URL"
        echo "  doctor  Check system health and fix dependencies"
        echo "  help    Show this help message"
        echo ""
        echo "Environment Variables (optional):"
        echo "  TRUETRACK_HOST      Host to bind (default: 127.0.0.1)"
        echo "  TRUETRACK_PORT      Port for Web UI (default: 8000)"
        echo "  TRUETRACK_DB_PATH   Path to SQLite DB"
        exit 0
        ;;

    *)
        echo "Usage: $0 {start|stop|status|doctor|help}"
        exit 1
        ;;
esac
