import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Literal

from core.config import Config

logger = logging.getLogger(__name__)

class AppConfig:
    """
    Centralized runtime configuration authority.
    Owns resolution of settings (DB -> Env -> Default).
    """
    
    _settings_table_initialized = False

    @classmethod
    def _init_settings_table(cls):
        """Ensure app_settings table exists."""
        if cls._settings_table_initialized:
            return

        db_path = Config.DB_PATH
        # Ensure parent dir exists
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass # handled downstream or already exists

        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                """)
                conn.commit()
            
            cls._settings_table_initialized = True
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize settings table: {e}")
            raise

    @classmethod
    def _get_db_value(cls, key: str) -> Optional[str]:
        cls._init_settings_table()
        try:
            with sqlite3.connect(Config.DB_PATH) as conn:
                row = conn.execute(
                    "SELECT value FROM app_settings WHERE key = ?",
                    (key,)
                ).fetchone()
                return row[0] if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to read setting {key} from DB: {e}")
            return None

    @classmethod
    def _set_db_value(cls, key: str, value: str) -> None:
        cls._init_settings_table()
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value)
            )
            conn.commit()

    @classmethod
    def get_music_library_root(cls) -> Path:
        """
        Resolve music library root.
        Order:
        1. DB (user selected)
        2. Env (MUSIC_LIBRARY_ROOT)
        3. OS Default
        """
        # 1. DB
        db_value = cls._get_db_value("music_library_root")
        if db_value:
            return Path(db_value)

        # 2. Env
        # Config.ENV_MUSIC_LIBRARY_ROOT is the raw env var
        if Config.ENV_MUSIC_LIBRARY_ROOT:
             return Path(Config.ENV_MUSIC_LIBRARY_ROOT).expanduser()

        # 3. Default
        # Windows: %USERPROFILE%\Music\TrueTrack
        # Linux/macOS: ~/Music/TrueTrack
        home = Path.home()
        # After resolving default
        default_path = home / "Music" / "TrueTrack"
        cls._set_db_value("music_library_root", str(default_path))
        return default_path

    @classmethod
    def set_music_library_root(cls, path: str) -> None:
        """
        Set and persist the music library root.
        Validates that the path is absolute and looks like a directory.
        """
        p = Path(path).resolve()
        if not p.is_absolute():
            raise ValueError("Path must be absolute")
        
        # Validate existence / creatability
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                 raise ValueError(f"Cannot create directory: {e}")
        
        if not os.access(p, os.W_OK):
             raise ValueError("Directory is not writable")

        cls._set_db_value("music_library_root", str(p))

    @classmethod
    def get_config_source(cls, key: str) -> Literal["db", "env", "default", "unknown"]:
        """Debug helper to know where a config came from."""
        if key == "music_library_root":
            if cls._get_db_value("music_library_root"):
                return "db"
            if Config.ENV_MUSIC_LIBRARY_ROOT:
                return "env"
            return "default"
        return "unknown"
