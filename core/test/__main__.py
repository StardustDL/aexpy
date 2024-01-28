import subprocess
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from zipfile import ZipFile
import wheel

TARGET_PACKAGE = "click"

CURRENT_DIR = Path(__file__).parent
TEMP_DIR = CURRENT_DIR / "temp"


@dataclass
class Input:
    wheel: Path
    src: Path


def prepare():
    os.makedirs(TEMP_DIR, exist_ok=True)
    subprocess.run(["pip", "download", "click==8.1.7"], cwd=TEMP_DIR, check=True)
    wheel = TEMP_DIR / "click-8.1.7-py3-none-any.whl"
    src = TEMP_DIR / "unpacked"
    with ZipFile(wheel, "r") as f:
        f.extractall(src)
    return Input(wheel, src)


if __name__ == "__main__":
    prepare()
