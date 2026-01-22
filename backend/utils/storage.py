import os
import shutil

from core.config import Config

LIBRARY_ROOT = Config.LIBRARY_ROOT


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def safe_filename(name: str) -> str:
    forbidden = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for ch in forbidden:
        name = name.replace(ch, "")
    return name.strip()
