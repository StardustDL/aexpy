import os
import pathlib
import shutil
from string import Template
from aexpy.analyses.models import ApiCollection
from aexpy.env import env
from aexpy import fsutils
from . import serializer
import subprocess
import sys

DOCKERFILE_TEMPLATE = Template("""FROM python:$pythonVersion

RUN [ "pip", "install", "mypy" ]

WORKDIR /app

ENTRYPOINT [ "python", "-u", "-m", "analyses" ]""")


def _hasImage(tag: str):
    return len(subprocess.run(["docker", "images", "-f", f"reference={tag}"], check=True, capture_output=True, text=True).stdout.strip().splitlines()) > 1


def getAnalysisImage(pythonVersion: str = 3.7, rebuild: bool = False):
    # rebuild = rebuild or env.dev

    cache = env.cache.joinpath("analysis")
    fsutils.ensureDirectory(cache)
    buildDirectory = cache.joinpath("build")
    fsutils.ensureDirectory(buildDirectory)
    dockerfile = cache.joinpath(f"{pythonVersion}.dockerfile")
    imageTag = f"aexpy-analysis:{pythonVersion}"

    if rebuild:
        if dockerfile.exists():
            os.remove(dockerfile)
        subprocess.call(["docker", "rmi", imageTag])

    if not dockerfile.exists():
        content = DOCKERFILE_TEMPLATE.substitute(
            pythonVersion=pythonVersion)
        dockerfile.write_text(content)

    if not _hasImage(imageTag):
        subprocess.run(["docker", "build", "-t", imageTag,
                              "-f", str(dockerfile.absolute().as_posix()), str(buildDirectory.absolute().as_posix())], check=True)

    return imageTag


def runAnalysis(image: str, packageFile: pathlib.Path, extractedPackage: pathlib.Path, topLevelModule: str) -> str:
    vols = [
        "-v",
        str(packageFile.absolute()) + ":" + f"/package/{packageFile.name}",
        "-v",
        str(extractedPackage.absolute()) + ":" + f"/package/unpacked",
    ]

    vols.append("-v")
    vols.append(str(pathlib.Path(__file__).parent.absolute()) +
                ":/app/analyses")

    result = subprocess.run(["docker", "run", "--rm", *[vol for vol in vols], image, packageFile.name, topLevelModule], check=True, stdout=subprocess.PIPE, text=True).stdout
    return result
    

def analyze(wheelfile: pathlib.Path):
    from ..downloads import wheels

    unpacked = wheels.unpackWheel(wheelfile)
    distinfo = wheels.getDistInfo(unpacked)

    name = distinfo.metadata.get("name").strip()
    version = distinfo.metadata.get("version")
    cache = env.cache.joinpath("analysis").joinpath("results").joinpath(name)
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{version}.json")
    if not cacheFile.exists():
        pythonVersion = wheels.getAvailablePythonVersion(distinfo)

        image = getAnalysisImage(pythonVersion, rebuild=False)
        result = runAnalysis(image, wheelfile, unpacked, distinfo.topLevel)

        cacheFile.write_text(result)

    return serializer.deserialize(cacheFile.read_text())