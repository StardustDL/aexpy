import code
from logging import Logger
import pathlib
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.reporting import Reporter as Base
from logging import Logger
from pathlib import Path
import subprocess
from uuid import uuid1
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.preprocessing import getDefault
from aexpy.extracting.environments import EnvirontmentExtractor, ExtractorEnvironment
from aexpy.differing.default import Differ as BaseDiffer
from aexpy.evaluating.default import Evaluator as BaseEvaluator
from aexpy.models import ApiBreaking, ApiDifference, Release, ApiDescription
from aexpy.pipelines import Pipeline

from datetime import datetime, timedelta
import json
from typing import Callable
import subprocess


class CondaEnvironment(ExtractorEnvironment):
    baseEnv: "dict[str, str]" = {}

    @classmethod
    def clearBase(cls):
        cls.reloadBase()
        for key, item in list(cls.baseEnv.items()):
            subprocess.run(
                f"conda remove -n {item} --all -y -q", shell=True, check=True, capture_output=True)
            del cls.baseEnv[key]

    @classmethod
    def reloadBase(cls):
        envs = json.loads(subprocess.run("conda env list --json", shell=True,
                          capture_output=True, text=True, check=True).stdout)["envs"]
        envs = [Path(item).name for item in envs]
        for item in envs:
            if item.startswith("pycompat-extbase-"):
                cls.baseEnv[item.removeprefix("pycompat-extbase-")] = item

    def __init__(self, pythonVersion: str = "3.7") -> None:
        super().__init__(pythonVersion)
        self.name = f"py{self.pythonVersion}-{uuid1()}"

    def run(self, command: str, **kwargs):
        return subprocess.run(f"conda activate {self.name} && {command}", **kwargs, shell=True)

    def __enter__(self):
        if not self.baseEnv:
            self.reloadBase()
        if self.pythonVersion not in self.baseEnv:
            baseName = f"pycompat-extbase-{self.pythonVersion}"
            subprocess.run(
                f"conda create -n {baseName} python={self.pythonVersion} -y -q", shell=True, check=True, capture_output=True)
            subprocess.run(
                f"conda activate {baseName} && python -m pip install parso", shell=True, check=True, capture_output=True)
            self.baseEnv[self.pythonVersion] = baseName
        subprocess.run(
            f"conda create -n {self.name} --clone {self.baseEnv[self.pythonVersion]} -y -q", shell=True, check=True, capture_output=True)
        subprocess.run(
            f"conda activate {self.name}", shell=True, check=True, capture_output=True)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            f"conda remove -n {self.name} --all -y -q", shell=True, capture_output=True, check=True)


class Extractor(EnvirontmentExtractor):
    def stage(self):
        return "pycompat-ext"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, env: "ExtractorEnvironment | None" = None) -> None:
        super().__init__(logger, cache, redo, CondaEnvironment)

    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess[str]]"):
        subres = run(f"python -m third.pycompat.raw", cwd=Path(__file__).parent.parent.parent,
                     text=True, capture_output=True, input=result.distribution.dumps())

        self.logger.info(f"Inner extractor exit with {subres.returncode}.")

        if subres.stdout.strip():
            self.logger.debug(f"STDOUT:\n{subres.stdout}")
        if subres.stderr.strip():
            self.logger.info(f"STDERR:\n{subres.stderr}")

        subres.check_returncode()
        data = json.loads(subres.stdout)
        result.load(data)


class Differ(BaseDiffer):
    def stage(self):
        return "pycompat-dif"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False) -> None:
        super().__init__(logger, cache, redo)
        self.rules.clear()

        from . import rules
        from aexpy.differing.rules import (modules, classes, functions,
                                           attributes, parameters, types, aliases, externals)

        self.rules.append(classes.AddClass)
        self.rules.append(classes.RemoveClass)
        self.rules.append(functions.AddFunction)
        self.rules.append(functions.RemoveFunction)
        self.rules.append(rules.AddRequiredParameter)
        self.rules.append(rules.RemoveRequiredParameter)
        self.rules.append(rules.ReorderParameter)
        self.rules.append(rules.AddOptionalParameter)
        self.rules.append(rules.RemoveOptionalParameter)
        self.rules.append(rules.AddParameterDefault)
        self.rules.append(rules.RemoveParameterDefault)
        self.rules.append(rules.ChangeParameterDefault)
        self.rules.append(attributes.AddAttribute)
        self.rules.append(attributes.RemoveAttribute)


class Evaluator(BaseEvaluator):
    def stage(self):
        return "pycompat-eva"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False) -> None:
        super().__init__(logger, cache, redo)

        self.evals.clear()
        from aexpy.evaluating.checkers import rankAt
        from aexpy.evaluating import evals

        self.evals.append(evals.AddClass)
        self.evals.append(evals.RemoveClass)
        self.evals.append(evals.AddFunction)
        self.evals.append(evals.RemoveFunction)
        self.evals.append(rankAt("AddRequiredParameter", BreakingRank.High))
        self.evals.append(rankAt("RemoveRequiredParameter", BreakingRank.High))
        self.evals.append(rankAt("ReorderParameter", BreakingRank.High))
        self.evals.append(rankAt("AddOptionalParameter", BreakingRank.High))
        self.evals.append(rankAt("RemoveOptionalParameter", BreakingRank.High))
        self.evals.append(rankAt("AddParameterDefault", BreakingRank.High))
        self.evals.append(rankAt("RemoveParameterDefault", BreakingRank.High))
        self.evals.append(rankAt("ChangeParameterDefault", BreakingRank.High))
        self.evals.append(evals.AddAttribute)
        self.evals.append(evals.RemoveAttribute)


class Reporter(Base):
    def stage(self):
        return "pycompat-rep"

    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        from aexpy.reporting.default import Reporter
        return Reporter(self.logger, self.cache, self.redo).report(oldRelease, newRelease, oldDistribution, newDistribution, oldDescription, newDescription, diff, bc)


def getPipeline():
    return Pipeline(extractor=Extractor(), differ=Differ(), evaluator=Evaluator(), reporter=Reporter())
