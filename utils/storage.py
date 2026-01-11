import os
import shutil

LIBRARY_ROOT = "/home/vicky/Music/library"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def safe_filename(name: str) -> str:
    forbidden = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for ch in forbidden:
        name = name.replace(ch, "")
    return name.strip()
