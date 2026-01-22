import os
import sys
import importlib
from pathlib import Path

# Set up paths
sys.path.append("/home/vicky/v_drive/Codes/TrueTrack")

def test_missing_env_var():
    print("TEST: Missing TRUETRACK_DB_PATH...")
    if "TRUETRACK_DB_PATH" in os.environ:
        del os.environ["TRUETRACK_DB_PATH"]
    
    # Reload config
    if "core.config" in sys.modules:
        del sys.modules["core.config"]
    
    try:
        from core.config import Config
        print("❌ FAILED: Config import should have failed but succeeded.")
        sys.exit(1)
    except RuntimeError as e:
        if "TRUETRACK_DB_PATH is required but not set" in str(e):
            print("✅ PASSED: Correctly raised RuntimeError.")
        else:
            print(f"❌ FAILED: Raised RuntimeError but message was wrong: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ FAILED: Raised wrong exception type: {type(e)}")
        sys.exit(1)

def test_present_env_var():
    print("\nTEST: Present TRUETRACK_DB_PATH...")
    test_path = "/tmp/test.db"
    os.environ["TRUETRACK_DB_PATH"] = test_path
    
    # Reload config
    if "core.config" in sys.modules:
        del sys.modules["core.config"]
        
    try:
        from core.config import Config
        if str(Config.DB_PATH) == test_path:
            print(f"✅ PASSED: Config.DB_PATH resolved to {test_path}")
        else:
            print(f"❌ FAILED: Config.DB_PATH = {Config.DB_PATH}, expected {test_path}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ FAILED: Unexpected exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_missing_env_var()
    test_present_env_var()
