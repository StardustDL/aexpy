from datetime import datetime
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).parent.parent.resolve()
PYTHON_SRC = ROOT / "src" / "aexpy"
INIT_FILE = PYTHON_SRC / "__init__.py"


def buildDate():
    data = datetime.now().isoformat()
    INIT_FILE.write_text(INIT_FILE.read_text().replace("<BUILD_DATE>", data))


def commitId():
    data = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    INIT_FILE.write_text(INIT_FILE.read_text().replace("<GIT_COMMIT>", data))


if __name__ == "__main__":
    buildDate()
    commitId()
