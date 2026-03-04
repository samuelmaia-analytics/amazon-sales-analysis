import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from scripts.run_pipeline import main

if __name__ == "__main__":
    main()
