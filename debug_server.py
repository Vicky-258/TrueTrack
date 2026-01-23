
import sys
import logging
from fastapi.staticfiles import StaticFiles

# Setup basic logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_staticfiles")

# Save original lookup
original_lookup = StaticFiles.lookup_path

def patched_lookup_path(self, path):
    full_path, stat_result = original_lookup(self, path)
    logger.info(f"StaticFiles Lookup: path={path}, directory={self.directory}, found={full_path}, stat={stat_result}")
    return full_path, stat_result

StaticFiles.lookup_path = patched_lookup_path
logger.info("Patched StaticFiles.lookup_path")

# Now import app and run it with uvicorn programmatically just for a quick test
# This is safer than modifying api/main.py directly with logging
from api.main import create_app
import uvicorn

if __name__ == "__main__":
    app = create_app(host="127.0.0.1", port=8001) # Use different port to avoid conflict
    logger.info("Starting debug server on 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
