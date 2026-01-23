import shutil
from pathlib import Path




def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def safe_filename(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "")
    return name.strip()
