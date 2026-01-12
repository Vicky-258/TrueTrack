def render_summary(job):
    result = job.result

    print()  # spacing

    if result.success:
        print("✔ Added to library")
        print("────────────────────────")
        print(f"Title   : {result.title}")
        print(f"Artist  : {result.artist}")
        if result.album:
            print(f"Album   : {result.album}")
        if result.source:
            print(f"Metadata: {result.source}")
        print(f"Path    : {result.path}")

    elif result.archived:
        print("⚠ Archived (unverified metadata)")
        print("───────────────────────────────")
        print(f"Title   : {result.title}")
        print(f"Artist  : {result.artist}")
        if result.reason:
            print(f"Reason  : {result.reason}")
        print(f"Path    : {result.path}")

    else:
        print("✖ Import failed")
        print("───────────────")
        if result.error:
            print(f"Reason : {result.error}")
        print("Hint   : Try --ask or --force-archive")
