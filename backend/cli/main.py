import argparse
import shutil
import sys

from core.job import Job, JobOptions
from core.states import PipelineState
from core.pipeline_factory import create_pipeline

from cli.renderer import CLIRenderer
from cli.summary import render_summary
from core.pipeline import PipelineError



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
# Interactive CLI entry
# -------------------------

def main():
    check_dependencies()

    parser = argparse.ArgumentParser(prog="music")
    parser.add_argument("query", help="Song name or search query")

    parser.add_argument("--ask", action="store_true", help="Ask before choosing song identity")
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

    renderer = CLIRenderer(job)
    pipeline = create_pipeline()

    # -------------------------
    # Control loop (HEART)
    # -------------------------

    while job.current_state not in (
        PipelineState.FINALIZED,
        PipelineState.FAILED,
    ):
        # 🔁 Advance exactly ONE pipeline step
        try:
            pipeline.step(job)
        except PipelineError as e:
            job.fail(e.code, e.message)
            break

        # 🟢 Flush progress message immediately
        if job.last_message:
            renderer.info(job.last_message)
            job.last_message = None

        # 🛑 Pause: user intent (YTMusic choice)
        if job.current_state == PipelineState.USER_INTENT_SELECTION:
            choice = renderer.request_intent_selection(job.source_candidates)

            if choice is None:
                job.fail("USER_ABORT", "User cancelled intent selection")
                break

            job.apply_identity_choice(job.source_candidates[choice])
            continue

        # 🛑 Pause: metadata ambiguity (iTunes)
        if job.current_state == PipelineState.USER_METADATA_SELECTION:
            choice = renderer.request_user_selection(job.metadata_candidates)

            if choice is None:
                job.fail("USER_ABORT", "User cancelled metadata selection")
                break

            job.apply_metadata_choice(choice)
            continue

    # -------------------------
    # Final summary
    # -------------------------

    render_summary(job)

    if job.current_state == PipelineState.FAILED:
        sys.exit(1)


if __name__ == "__main__":
    main()
