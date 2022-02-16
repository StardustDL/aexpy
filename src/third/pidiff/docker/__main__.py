from pathlib import Path
import subprocess


def DOCKERFILE_TXT(pyver): return f"""
FROM python:{pyver}

RUN ["pip", "install", "virtualenv", "pidiff"]

ENTRYPOINT [ "pidiff" ]
"""


def build():
    for i in range(7, 11):
        pyver = f"3.{i}"
        file = Path(__file__).parent / f"py{pyver}.Dockerfile"
        file.write_text(DOCKERFILE_TXT(pyver))

        print(f"Building {pyver} @ {file}")

        subprocess.run(["docker", "build", "-t",
                       f"pidiff:{pyver}", "-f", file.name, "."], cwd=Path(__file__).parent, check=True)


if __name__ == "__main__":
    build()
