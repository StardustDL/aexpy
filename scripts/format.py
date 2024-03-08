from pathlib import Path
import subprocess

ROOT = Path(__file__).parent.parent.resolve()
PYTHON_SRC = ROOT / "src" / "aexpy"


def black():
    subprocess.run(["black", str(PYTHON_SRC)], check=True)


def isort():
    subprocess.run(["isort", str(PYTHON_SRC)], check=True)


if __name__ == "__main__":
    black()
    isort()
