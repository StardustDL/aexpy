import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    subprocess.run(
        [sys.executable, "-m", "aexpy"] + sys.argv[1:], cwd=Path(__file__).parent.parent / "src"
    )
