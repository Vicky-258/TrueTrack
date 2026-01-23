
from pathlib import Path
import os

def check_paths():
    # Simulate the logic in api/main.py (assuming this script is run from project root)
    # api/main.py is in api/
    
    current_file = Path("api/main.py").resolve()
    print(f"Simulated __file__: {current_file}")
    
    project_root = current_file.parent.parent
    print(f"Project Root: {project_root}")
    
    frontend_dir = project_root / "frontend"
    next_static_dir = frontend_dir / ".next" / "static"
    
    print(f"Target Static Dir: {next_static_dir}")
    print(f"Exists? {next_static_dir.exists()}")
    
    if next_static_dir.exists():
        print("Listing first 5 files in static dir:")
        try:
             # It's a directory with subdirs usually
            for i, p in enumerate(next_static_dir.glob("**/*")):
                if i > 5: break
                print(f" - {p.relative_to(next_static_dir)}")
        except Exception as e:
            print(f"Error listing: {e}")
    else:
        print(f"Files found in {frontend_dir / '.next'}:")
        try:
            for p in (frontend_dir / ".next").iterdir():
                print(f" - {p.name}")
        except Exception as e:
            print(f"Error listing .next: {e}")

if __name__ == "__main__":
    check_paths()
