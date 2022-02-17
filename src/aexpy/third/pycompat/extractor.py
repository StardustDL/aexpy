import code
from logging import Logger
import pathlib
from aexpy import getCacheDirectory
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.reporting import Reporter as Base
from logging import Logger
from pathlib import Path
import subprocess
from uuid import uuid1
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.preprocessing import getDefault
from aexpy.extracting.environments import EnvirontmentExtractor, ExtractorEnvironment
from aexpy.extracting.environments.conda import CondaEnvironment
from aexpy.differing.default import Differ as BaseDiffer
from aexpy.evaluating.default import Evaluator as BaseEvaluator
from aexpy.models import ApiBreaking, ApiDifference, Release, ApiDescription
from aexpy.pipelines import Pipeline

from datetime import datetime, timedelta
import json
from typing import Callable
import subprocess


class PycompatEnvironment(CondaEnvironment):
    __baseenvprefix__ = "pycompat-extbase-"
    __envprefix__ = "pycompat-ext-"
    __packages__ = ["parso"]


class Extractor(EnvirontmentExtractor):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, cached: "bool" = True, env: "ExtractorEnvironment | None" = None) -> None:
        super().__init__(logger, cache or getCacheDirectory() / "pycompat" /
                         "extracting", redo, cached, env or PycompatEnvironment)

    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess[str]]"):
        subres = run(f"python -m aexpy.third.pycompat.raw", text=True,
                     capture_output=True, input=result.distribution.dumps())

        self.logger.info(f"Inner extractor exit with {subres.returncode}.")

        if subres.stdout.strip():
            self.logger.debug(f"STDOUT:\n{subres.stdout}")
        if subres.stderr.strip():
            self.logger.info(f"STDERR:\n{subres.stderr}")

        subres.check_returncode()
        data = json.loads(subres.stdout)
        result.load(data)
