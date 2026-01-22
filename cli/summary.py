def render_summary(job):
    result = job.result

    print()  # spacing

    # -------------------------
    # Success
    # -------------------------
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
        return

    # -------------------------
    # File already exists
    # -------------------------
    if job.error_code == "FILE_EXISTS":
        print("⚠ Track already exists")
        print("──────────────────────")
        if result.path:
            print(f"Path : {result.path}")
        print("Hint : Delete/rename the file, or use --force-archive")
        return

    # -------------------------
    # Archived (fallback)
    # -------------------------
    if result.archived:
        print("⚠ Archived (unverified metadata)")
        print("───────────────────────────────")
        print(f"Title   : {result.title}")
        print(f"Artist  : {result.artist}")
        if result.reason:
            print(f"Reason  : {result.reason}")
        print(f"Path    : {result.path}")
        return

    # -------------------------
    # Generic failure
    # -------------------------
    print("✖ Import failed")
    print("───────────────")

    if job.error_message:
        print(f"Reason : {job.error_message}")
    elif result.error:
        print(f"Reason : {result.error}")

    print("Hint   : Try --ask or --force-archive")
