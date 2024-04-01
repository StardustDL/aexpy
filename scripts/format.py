from pathlib import Path
import subprocess

ROOT = Path(__file__).parent.parent.resolve()
AEXPY_SRC = ROOT / "src" / "aexpy"
SERVER_SRC = ROOT / "src" / "servers"
SRCS = [AEXPY_SRC, SERVER_SRC]


def black():
    for src in SRCS:
        subprocess.run(["black", str(src)], check=True)


def isort():
    for src in SRCS:
        subprocess.run(["isort", str(src)], check=True)


if __name__ == "__main__":
    black()
    isort()
