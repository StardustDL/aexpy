from datetime import datetime
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).parent.parent

webDist = root / "src" / "web" / "dist"
webEnv = root / "src" / "web" / ".env"
serverWww = root / "src" / "servers" / "wwwroot"


def build():
    originalText = webEnv.read_text()
    webEnv.write_text(
        f"""
VITE_NOSERVER=0
VITE_COMMIT_ID=on-line
VITE_BUILD_DATE={datetime.now().isoformat()}
"""
    )
    subprocess.run("npm run build", shell=True, cwd=webDist.parent, check=True)
    webEnv.write_text(originalText)


def copy():
    shutil.rmtree(serverWww)
    shutil.copytree(webDist, serverWww)


if __name__ == "__main__":
    build()
    copy()
