import code
import pathlib
import subprocess
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path
from typing import Callable, Type
from uuid import uuid1

from aexpy import getAppDirectory, json
from aexpy.environments.conda import CondaEnvironment
from aexpy.extracting.environments import (EnvirontmentExtractor,
                                           ExecutionEnvironment)
from aexpy.models import (ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.description import TRANSFER_BEGIN
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline
from aexpy.producers import ProducerOptions
from aexpy.reporting import Reporter as Base


class PycompatEnvironment(CondaEnvironment):
    __baseenvprefix__ = "pycompat-extbase-"
    __envprefix__ = "pycompat-ext-"
    __packages__ = ["parso"]


class Extractor(EnvirontmentExtractor):
    def __init__(self, logger: "Logger | None" = None, env: "Type[ExecutionEnvironment] | None" = None) -> None:
        super().__init__(logger, env or PycompatEnvironment)

    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess[str]]"):
        assert result.distribution
        subres = run(f"python -m aexpy.third.pycompat.raw", text=True,
                     capture_output=True, input=result.distribution.dumps(), cwd=getAppDirectory().parent)

        self.logger.info(f"Inner extractor exit with {subres.returncode}.")

        if subres.stdout.strip():
            self.logger.debug(f"STDOUT:\n{subres.stdout}")
        if subres.stderr.strip():
            self.logger.info(f"STDERR:\n{subres.stderr}")

        subres.check_returncode()
        data = subres.stdout.split(TRANSFER_BEGIN, 1)[1]
        data = json.loads(data)
        result.load(data)
