"""Package the current direct-mount Nano enclosure files and verification."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent.parent/'nano-esp32/package_current.py'), run_name="__main__")
