import os
import pathlib
import shutil
import subprocess
import sys
from string import Template

from aexpy import fsutils
from aexpy.analyses.models import ApiCollection
from aexpy.env import env

from .. import get_app_directory
from . import serializer

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


def runInnerAnalysis(image: str, packageFile: pathlib.Path, extractedPackage: pathlib.Path, topLevelModule: str) -> str:
    packageFile = packageFile.absolute()
    extractedPackage = extractedPackage.absolute()
    srcPath = pathlib.Path(__file__).parent.absolute()

    if env.docker.enable:
        packageFile = env.docker.hostCache.joinpath(
            packageFile.relative_to(env.cache))
        extractedPackage = env.docker.hostCache.joinpath(
            extractedPackage.relative_to(env.cache))
        srcPath = env.docker.hostSrc.joinpath(
            srcPath.relative_to(get_app_directory()))

    vols = [
        "-v",
        str(packageFile.absolute()) + ":" + f"/package/{packageFile.name}",
        "-v",
        str(extractedPackage.absolute()) + ":" + f"/package/unpacked",
    ]

    vols.append("-v")
    vols.append(str(srcPath) +
                ":/app/analyses")

    result = subprocess.run(["docker", "run", "--rm", *[vol for vol in vols], image,
                            packageFile.name, topLevelModule], check=True, stdout=subprocess.PIPE, text=True).stdout
    return result


def enrich(api: ApiCollection):
    from .enriching import kwargs

    kwargs.KwargsEnricher().enrich(api)


def analyze(wheelfile: pathlib.Path):
    from ..downloads import wheels

    unpacked = wheels.unpackWheel(wheelfile)
    distinfo = wheels.getDistInfo(unpacked)
    if distinfo is None:
        raise Exception(f"No distinfo for {wheelfile}.")

    name = distinfo.metadata.get("name").strip()
    version = distinfo.metadata.get("version")
    cache = env.cache.joinpath("analysis").joinpath("results").joinpath(name)
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{version}.json")
    if not cacheFile.exists() or env.redo:
        pythonVersion = wheels.getAvailablePythonVersion(distinfo)

        image = getAnalysisImage(pythonVersion)
        data = runInnerAnalysis(image, wheelfile, unpacked, distinfo.topLevel)

        result = serializer.deserialize(data)
        enrich(result)

        cacheFile.write_text(serializer.serialize(result))
        return result

    return serializer.deserialize(cacheFile.read_text())
