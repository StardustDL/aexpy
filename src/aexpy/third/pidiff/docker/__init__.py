import subprocess
from pathlib import Path


def DOCKERFILE_TXT(pyver): return f"""
FROM python:{pyver}

RUN ["pip", "install", "virtualenv", "pidiff"]

ENTRYPOINT [ "pidiff" ]
"""


def buildVersion(repo: "str", version: "str") -> "str":
    file = Path(__file__).parent / f"py{version}.Dockerfile"
    file.write_text(DOCKERFILE_TXT(version))

    tag = f"{repo}:{version}"

    subprocess.run(["docker", "build", "-t",
                    tag, "-f", file.name, "."], cwd=Path(__file__).parent, check=True)

    return tag
