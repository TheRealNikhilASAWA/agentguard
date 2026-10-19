"""Cross-platform equivalent of `make test`."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=root))
