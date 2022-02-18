import code
from logging import Logger
import pathlib
from aexpy import getCacheDirectory
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.producer import ProducerOptions
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
from aexpy.evaluating.default import RuleEvaluator
from aexpy.models import ApiBreaking, ApiDifference, Release, ApiDescription
from aexpy.pipelines import Pipeline

from datetime import datetime, timedelta
import json
from typing import Callable
import subprocess


class Evaluator(RuleEvaluator):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "pycompat" / "evaluating"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[RuleEvaluator] | None" = None) -> None:
        rules = rules or []

        from aexpy.evaluating.checkers import rankAt
        from aexpy.evaluating import evals

        rules.append(evals.AddClass)
        rules.append(evals.RemoveClass)
        rules.append(evals.AddFunction)
        rules.append(evals.RemoveFunction)
        rules.append(rankAt("AddRequiredParameter", BreakingRank.High))
        rules.append(rankAt("RemoveRequiredParameter", BreakingRank.High))
        rules.append(rankAt("ReorderParameter", BreakingRank.High))
        rules.append(rankAt("AddOptionalParameter", BreakingRank.High))
        rules.append(rankAt("RemoveOptionalParameter", BreakingRank.High))
        rules.append(rankAt("AddParameterDefault", BreakingRank.High))
        rules.append(rankAt("RemoveParameterDefault", BreakingRank.High))
        rules.append(rankAt("ChangeParameterDefault", BreakingRank.High))
        rules.append(evals.AddAttribute)
        rules.append(evals.RemoveAttribute)

        super().__init__(logger, cache, options, rules)
