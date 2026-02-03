import sys
import os
import shutil
import subprocess
import importlib.metadata
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Formatting Helpers
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{msg}{Colors.ENDC}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg: str):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(key: str, value: str):
    print(f"  {key:<20} {Colors.CYAN}{value}{Colors.ENDC}")

# --- Checks ---

def check_python() -> bool:
    print_header("System Environment")
    
    # 1. Python Path
    print_info("Python Executable", sys.executable)
    
    # 2. Virtualenv
    is_venv = (sys.prefix != sys.base_prefix)
    if is_venv:
        print_success("Virtualenv active")
    else:
        print_warning("Not running in a virtualenv (Recommended)")
        
    return True

def check_config() -> str:
    print_header("Configuration")
    
    status = "GOOD"
    
    # 1. DB Path (Safe Check)
    db_path_env = os.environ.get("TRUETRACK_DB_PATH")
    if db_path_env:
        print_info("TRUETRACK_DB_PATH", db_path_env)
        db_path = Path(db_path_env)
        if not db_path.parent.exists():
             print_warning(f"Parent directory does not exist: {db_path.parent}")
             status = "DEGRADED"
    else:
        print_error("TRUETRACK_DB_PATH is not set in environment")
        status = "BROKEN"

    # 2. Temp Directory
    # We try to import AppConfig but catch errors if DB is broken
    try:
        from core.app_config import AppConfig
        # We don't have a direct method for temp dir in AppConfig usually, 
        # it's dynamically created. We can check if we can import it.
        # Let's check Music Library instead as per prompt.
        try:
            lib_root = AppConfig.get_music_library_root()
            print_info("Music Library", str(lib_root))
            if os.access(lib_root, os.W_OK):
                print_success("Music library is writable")
            else:
                print_error(f"Music library is NOT writable: {lib_root}")
                status = "BROKEN"
        except Exception as e:
            print_error(f"Failed to resolve Music Library: {e}")
            status = "BROKEN"
            
    except Exception as e:
        print_error(f"Could list load AppConfig: {e}")
        status = "BROKEN"

    return status

def get_yt_dlp_version() -> Tuple[Optional[str], Optional[str]]:
    """Returns (version_string, error_message)"""
    try:
        dist = importlib.metadata.distribution("yt-dlp")
        return dist.version, None
    except importlib.metadata.PackageNotFoundError:
        return None, "Not installed in current environment"

def check_tools() -> str:
    print_header("External Tools")
    
    status = "GOOD"
    
    # --- yt-dlp ---
    version, err = get_yt_dlp_version()
    if version:
        print_info("yt-dlp", version)
        
        # Age check (heuristic)
        # yt-dlp uses YYYY.MM.DD versioning
        try:
            date_part = ".".join(version.split(".")[:3])
            ver_date = datetime.strptime(date_part, "%Y.%m.%d")
            age = (datetime.now() - ver_date).days
            
            if age > 90:
                print_warning(f"yt-dlp is {age} days old. Recommended to update.")
                print(f"    {Colors.WARNING}Run: truetrack doctor --fix yt-dlp{Colors.ENDC}")
                status = "DEGRADED" if status == "GOOD" else status
            else:
                print_success("yt-dlp is up-to-date (ish)")
                
        except ValueError:
            # Version parsing failed, maybe non-standard version
            pass
            
    else:
        print_error(f"yt-dlp missing: {err}")
        status = "BROKEN"

    # --- ffmpeg ---
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print_info("ffmpeg", ffmpeg_path)
        print_success("ffmpeg is available")
    else:
        print_error("ffmpeg not found in PATH")
        print("    Please install ffmpeg usage your system package manager.")
        status = "BROKEN"

    return status


# --- Fixes ---

def fix_yt_dlp():
    print_header("Fixing: yt-dlp")
    
    current_ver, _ = get_yt_dlp_version()
    print(f"Current version: {current_ver or 'None'}")
    
    print(f"\n{Colors.BOLD}Why update?{Colors.ENDC}")
    print("Frequent updates are required to handle YouTube changes and prevent download failures.\n")

    cmd = ["uv", "pip", "install", "-U", "yt-dlp"]
    print(f"Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print_success("Update command finished.")
        
        # Verify
        # Reloading metadata in the same process might be tricky if cached, 
        # but usage usually spawns new processes, so just checking metadata is fine.
        # Actually importlib.metadata might cache. Let's try to reload.
        importlib.invalidate_caches()
        new_ver, _ = get_yt_dlp_version()
        print(f"New version: {new_ver}")
        
        if current_ver != new_ver:
             print_success("yt-dlp successfully updated.")
        else:
             print_warning("Version did not change. Already latest?")
             
    except subprocess.CalledProcessError as e:
        print_error(f"Update failed with code {e.returncode}")
        sys.exit(1)

def fix_ffmpeg():
    print_header("Fixing: ffmpeg")
    print_error("Automated installation of ffmpeg is not supported.")
    print("Please install it manually:")
    print("  sudo apt install ffmpeg   # Debian/Ubuntu")
    print("  brew install ffmpeg       # macOS")
    sys.exit(1)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="TrueTrack System Doctor")
    parser.add_argument("--fix", choices=["yt-dlp", "ffmpeg"], help="Attempt to fix a specific tool")
    args = parser.parse_args()

    if args.fix == "yt-dlp":
        fix_yt_dlp()
        return
    elif args.fix == "ffmpeg":
        fix_ffmpeg()
        return

    # Read-only mode
    print(f"{Colors.BOLD}TrueTrack Doctor 🩺{Colors.ENDC}")
    
    check_python()
    cfg_status = check_config()
    tool_status = check_tools()
    
    print("\n" + "-"*40)
    
    final_status = "GOOD"
    if cfg_status == "BROKEN" or tool_status == "BROKEN":
        final_status = "BROKEN"
    elif cfg_status == "DEGRADED" or tool_status == "DEGRADED":
        final_status = "DEGRADED"
        
    if final_status == "GOOD":
        print(f"System Status: {Colors.GREEN}{Colors.BOLD}GOOD{Colors.ENDC}")
        print("Everything looks healthy.")
    elif final_status == "DEGRADED":
        print(f"System Status: {Colors.WARNING}{Colors.BOLD}DEGRADED{Colors.ENDC}")
        print("System functionality may be impaired.")
    else:
        print(f"System Status: {Colors.FAIL}{Colors.BOLD}BROKEN{Colors.ENDC}")
        print("Critical dependencies are missing or misconfigured.")
        sys.exit(1)

if __name__ == "__main__":
    main()
