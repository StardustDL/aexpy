from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).parent.parent

mainSrc = root / "src" / "aexpy"
toolSrc = mainSrc / "tools"
serverSrc = root / "src" / "servers"

webDist = root / "src" / "web" / "dist"
serverWww = serverSrc / "wwwroot"


def frontend():
    shutil.rmtree(serverWww)
    shutil.copytree(webDist, serverWww)


def server():
    target = toolSrc / "servers"
    shutil.copytree(serverSrc, target)


if __name__ == "__main__":
    frontend()
    server()
