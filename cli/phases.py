from enum import Enum

class CLIPhase(Enum):
    IDENTIFYING = "🔍 Identifying track"
    DOWNLOADING = "⬇️  Downloading audio"
    PROCESSING = "🎧 Processing audio"
    MATCHING = "🧠 Matching official metadata"
    USER_INPUT = "👤 Waiting for user selection"
    ARCHIVED = "⚠️  Archived (unverified)"
    STORING = "📦 Saving to library"
    DONE = "✔ Done"
