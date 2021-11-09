from dataclasses import dataclass
from datetime import timedelta
import os
import pathlib
import shutil
import subprocess
import sys
from string import Template
from typing import Tuple
from timeit import default_timer as timer

from aexpy import fsutils
from aexpy.analyses.models import ApiCollection
from aexpy.downloads.wheels import DistInfo
from aexpy.env import env
from aexpy.logging.models import PayloadLog
from aexpy.logging import serializer as logserializer

from .. import get_app_directory
from . import serializer, OUTPUT_PREFIX

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


def runInnerAnalysis(image: str, packageFile: pathlib.Path, extractedPackage: pathlib.Path, topLevelModule: str) -> Tuple[str | None, PayloadLog]:
    log = PayloadLog()

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

    startTime = timer()

    result = subprocess.run(["docker", "run", "--rm", *[vol for vol in vols], image,
                            packageFile.name, topLevelModule], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    endTime = timer()

    log.output = result.stdout
    log.error = result.stderr
    log.duration = timedelta(seconds=endTime - startTime)

    if result.returncode == 0:
        data = result.stdout.split(OUTPUT_PREFIX, maxsplit=1)[-1]
        return data, log
    else:
        return None, log


def enrich(api: ApiCollection):
    from .enriching import kwargs

    kwargs.KwargsEnricher().enrich(api)


@dataclass
class AnalysisInfo:
    wheel: pathlib.Path
    unpacked: pathlib.Path
    distinfo: DistInfo
    cache: pathlib.Path
    log: pathlib.Path


def prepare(wheelfile: pathlib.Path) -> AnalysisInfo:
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
    logFile = cache.joinpath(f"{version}.log.json")

    return AnalysisInfo(wheel=wheelfile, unpacked=unpacked, distinfo=distinfo, cache=cacheFile, log=logFile)


def analyze(wheelfile: pathlib.Path) -> ApiCollection | None:
    from ..downloads import wheels

    info = prepare(wheelfile)

    if not info.cache.exists() or env.redo:
        pythonVersion = wheels.getAvailablePythonVersion(info.distinfo)

        image = getAnalysisImage(pythonVersion)
        data, log = runInnerAnalysis(
            image, wheelfile, info.unpacked, info.distinfo.topLevel)

        if data is not None:
            result = serializer.deserialize(data)

            startTime = timer()

            enrich(result)

            endTime = timer()

            log.duration = timedelta(seconds=log.duration.total_seconds() + (endTime - startTime))

            info.log.write_text(logserializer.serialize(log))

            info.cache.write_text(serializer.serialize(result))

            return result
        else:
            info.log.write_text(logserializer.serialize(log))

            return None

    return serializer.deserialize(info.cache.read_text())


def getLog(wheelfile: pathlib.Path) -> PayloadLog | None:
    info = prepare(wheelfile)
    if info.log.exists():
        return logserializer.deserialize(info.log.read_text())
    return None
