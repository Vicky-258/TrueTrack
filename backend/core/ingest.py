import argparse
import shutil
import sys

from core.job import Job, JobOptions
from core.states import PipelineState
from core.pipeline_factory import create_pipeline
from cli.summary import render_summary


# -------------------------
# Dependency check
# -------------------------

def check_dependencies():
    required = ["ffmpeg", "yt-dlp"]
    missing = [tool for tool in required if not shutil.which(tool)]

    if missing:
        print("❌ CRITICAL: Missing dependencies:")
        for tool in missing:
            print(f"   - {tool}")
        print("\nPlease install them and ensure they are in your PATH.")
        sys.exit(1)


# -------------------------
# Entry point (non-interactive)
# -------------------------

def main():
    check_dependencies()

    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("query", help="Song name or search query")

    parser.add_argument("--ask", action="store_true", help="Require explicit user intent (will pause)")
    parser.add_argument("--verbose", action="store_true", help="Show engine logs")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without downloading")
    parser.add_argument("--force-archive", action="store_true", help="Skip metadata matching")

    args = parser.parse_args()

    options = JobOptions(
        ask=args.ask,
        verbose=args.verbose,
        dry_run=args.dry_run,
        force_archive=args.force_archive,
    )

    job = Job(
        options=options,
        raw_query=args.query,
        normalized_query=args.query.lower(),
    )

    pipeline = create_pipeline()
    pipeline.run(job)

    # -------------------------
    # Handle paused states
    # -------------------------

    if job.current_state.name.startswith("USER_"):
        print("✖ Import paused — user input required")
        print(f"State  : {job.current_state.name}")
        print("Hint   : Use the interactive CLI or API to continue")
        sys.exit(2)

    # -------------------------
    # Final result
    # -------------------------

    render_summary(job)

    if job.current_state == PipelineState.FAILED:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
