import os
import pathlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import timedelta
from io import StringIO
from logging import StreamHandler
from string import Template
from timeit import default_timer as timer
from typing import Tuple

import logging

from aexpy import utils
from aexpy.analyses.enriching import AnalysisInfo
from aexpy.analyses.models import ApiCollection
from aexpy.downloads.wheels import DistInfo
from aexpy.env import env
from aexpy.logging import serializer as logserializer
from aexpy.logging.models import PayloadLog

from .. import get_app_directory
from . import LOGGING_DATEFMT, LOGGING_FORMAT, OUTPUT_PREFIX, serializer

DOCKERFILE_TEMPLATE = Template("""FROM python:$pythonVersion

RUN [ "pip", "install", "mypy" ]

WORKDIR /app

ENTRYPOINT [ "python", "-u", "-m", "analyses" ]""")

logger = logging.getLogger("analysis")

def runInnerAnalysis(image: str, packageFile: pathlib.Path, extractedPackage: pathlib.Path, topLevelModule: list[str]) -> Tuple[str | None, PayloadLog]:
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

    args = ["docker", "run", "--rm", *[vol for vol in vols], image,
            packageFile.name, ",".join(topLevelModule), str(env.verbose)]
    logger.info(f"Inner analyze {packageFile}")
    logger.debug(f"Inner analysis args: {args}")

    startTime = timer()

    result = subprocess.run(
        args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    endTime = timer()

    log.output = result.stdout
    log.error = result.stderr
    log.duration = timedelta(seconds=endTime - startTime)

    logger.info(
        f"Inner analyzed {packageFile} with exitcode {result.returncode}, cost {log.duration}.")

    if result.returncode == 0:
        data = result.stdout.split(OUTPUT_PREFIX, maxsplit=1)[-1]
        return data, log
    else:
        return None, log
