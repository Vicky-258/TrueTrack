from core.job import Job, JobOptions
from core.states import PipelineState
from core.pipeline import (
    Pipeline,
    handle_init,
    handle_searching,
    handle_downloading,
    handle_extracting,
    handle_matching_metadata,
    handle_tagging,
    handle_storage,
    handle_resolving_identity,
    handle_metadata_user_selection,
    handle_archiving,
    handle_user_intent_selection
)
import shutil
import sys
from cli.renderer import CLIRenderer
from cli.summary import render_summary
import argparse



def check_dependencies():
    required = ["ffmpeg", "yt-dlp"]
    missing = [tool for tool in required if not shutil.which(tool)]
    
    if missing:
        print("❌ CRITICAL: Missing dependencies:")
        for tool in missing:
            print(f"   - {tool}")
        print("\nPlease install them and ensure they are in your PATH.")
        sys.exit(1)


def main():
    check_dependencies()

    parser = argparse.ArgumentParser(prog="music")
    parser.add_argument("query", help="Song name or search query")

    parser.add_argument("--ask", action="store_true", help="Always ask user to choose metadata")
    parser.add_argument("--verbose", action="store_true", help="Show engine logs")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without downloading or writing files")
    parser.add_argument("--force-archive", action="store_true", help="Skip metadata matching and archive directly")

    args = parser.parse_args()

    options = JobOptions(
        ask=args.ask,
        verbose=args.verbose,
        dry_run=args.dry_run,
        force_archive=args.force_archive,
    )

    job = Job(
        options=options,                  # ✅ REQUIRED
        raw_query=args.query,
        normalized_query=args.query.lower(),
    )

    renderer = CLIRenderer(job)
    pipeline = Pipeline(renderer=renderer)

    pipeline.register(PipelineState.INIT, handle_init)
    pipeline.register(PipelineState.RESOLVING_IDENTITY, handle_resolving_identity)
    pipeline.register(PipelineState.SEARCHING, handle_searching)
    pipeline.register(PipelineState.DOWNLOADING, handle_downloading)
    pipeline.register(PipelineState.EXTRACTING, handle_extracting)
    pipeline.register(PipelineState.MATCHING_METADATA, handle_matching_metadata)
    pipeline.register(PipelineState.USER_METADATA_SELECTION, handle_metadata_user_selection)
    pipeline.register(PipelineState.USER_INTENT_SELECTION, handle_user_intent_selection)
    pipeline.register(PipelineState.ARCHIVING, handle_archiving)
    pipeline.register(PipelineState.TAGGING, handle_tagging)
    pipeline.register(PipelineState.STORING, handle_storage)

    pipeline.run(job)
    render_summary(job)


if __name__ == "__main__":
    main()
