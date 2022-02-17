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


class Evaluator(BaseEvaluator):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, cached: "bool" = True) -> None:
        super().__init__(logger, cache or getCacheDirectory() /
                         "pycompat" / self.stage(), redo, cached)

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
