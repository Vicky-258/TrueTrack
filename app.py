import os
import logging
import uvicorn

from api.main import create_app


def main() -> None:
    """
    Canonical entrypoint for TrueTrack.

    Responsibilities:
    - load runtime config from env
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

    app = create_app()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=False,
    )


if __name__ == "__main__":
    main()
