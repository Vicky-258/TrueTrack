from datetime import datetime

EMOJIS = {
    "INIT": "🚀",
    "SEARCHING": "🔍",
    "DOWNLOADING": "⬇️",
    "EXTRACTING": "🎧",
    "MATCHING_METADATA": "🧠",
    "TAGGING": "🏷️",
    "STORING": "📁",
    "FINALIZED": "✅",
    "FAILED": "❌",
}

def section(title: str):
    print("\n" + "=" * 60)
    print(f"{title}")
    print("=" * 60)

def step(state: str, msg: str = ""):
    emoji = EMOJIS.get(state, "➡️")
    print(f"\n{emoji} [{state}] {msg}")

def kv(key: str, value):
    print(f"   • {key:<18}: {value}")

def list_item(idx: int, title: str, score=None, flags=None):
    line = f"{idx:>2}. {title}"
    if score is not None:
        line += f"  (score={score})"
    print(line)
    if flags:
        print(f"      flags : {', '.join(flags)}")

def success(msg: str):
    print(f"\n✅ {msg}")

def warn(msg: str):
    print(f"\n⚠️  {msg}")

def error(msg: str):
    print(f"\n❌ {msg}")
