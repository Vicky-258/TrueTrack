import os
import logging
import signal
import sys
import threading
from typing import NoReturn

# Add project root to path
# This allows imports like 'infra.sqlite_job_store' to work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from infra.sqlite_job_store import SqliteJobStore
from worker.runtime import WorkerRuntime

def main() -> None:
    """
    Entry point for the standalone worker process.
    """
    # Configure logging
    log_level = os.getenv("TRUETRACK_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="[WORKER] %(asctime)s | %(levelname)s | %(message)s",
    )

    # Resolve DB path
    # Must match the app.py / install script convention
    db_path = os.getenv("TRUETRACK_DB_PATH")
    if not db_path:
        logging.error("TRUETRACK_DB_PATH env var is required")
        sys.exit(1)

    logging.info(f"Starting Worker (DB: {db_path})...")

    # Initialize infrastructure
    try:
        # We don't need to run migrations here as the API/Installer handles that
        # But for robustness, we could, but let's assume schema exists.
        store = SqliteJobStore(db_path)
    except Exception as e:
        logging.critical(f"Failed to initialize JobStore: {e}")
        sys.exit(1)

    # Initialize Runtime
    runtime = WorkerRuntime(store)
    runtime.start()

    # Graceful Shutdown
    shutdown_event = threading.Event()

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, stopping...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Block main thread until signal
    shutdown_event.wait()
    
    logging.info("Stopping worker runtime...")
    runtime.stop()
    logging.info("Worker exit.")

if __name__ == "__main__":
    main()
