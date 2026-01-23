import os
import logging
import subprocess
import signal

import uvicorn

from api.main import create_app


def start_next_standalone() -> subprocess.Popen:
    """
    Start Next.js standalone server as an internal subprocess.
    This server is NOT exposed publicly.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(project_root, "frontend")
    server_js = os.path.join(frontend_dir, ".next", "standalone", "server.js")

    if not os.path.exists(server_js):
        raise RuntimeError(
            "Next.js standalone server not found.\n"
            "Expected: frontend/.next/standalone/server.js\n"
            "Did you run the installer / pnpm build?"
        )

    env = os.environ.copy()
    env["HOSTNAME"] = "127.0.0.1"
    env["PORT"] = "3001"

    return subprocess.Popen(
        ["node", server_js],
        cwd=frontend_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    """
    Canonical entrypoint for TrueTrack.

    Responsibilities:
    - load runtime config from env
    - start internal Next.js frontend
    - create FastAPI app
    - start ASGI server
    """

    host = os.getenv("TRUETRACK_HOST", "127.0.0.1")
    port = int(os.getenv("TRUETRACK_PORT", "8000"))
    log_level = os.getenv("TRUETRACK_LOG_LEVEL", "info")

    logging.basicConfig(
        level=log_level.upper(),
        format="[TRUETRACK] %(asctime)s | %(levelname)s | %(message)s",
    )

    logging.info("Starting Next.js frontend (standalone)...")
    next_proc = start_next_standalone()

    def shutdown_handler(*_):
        logging.info("Shutting down Next.js frontend...")
        next_proc.terminate()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    app = create_app(host=host, port=port)

    logging.info("Starting FastAPI backend...")
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=False,
        )
    finally:
        shutdown_handler()


if __name__ == "__main__":
    main()
