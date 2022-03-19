import code
import pathlib
import subprocess
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import getCacheDirectory, json
from aexpy.differing.default import Differ as BaseDiffer
from aexpy.environments.conda import CondaEnvironment
from aexpy.evaluating.default import RuleEvaluator
from aexpy.evaluating.checkers import EvalRule
from aexpy.extracting.environments import (EnvirontmentExtractor,
                                           ExecutionEnvironment)
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline
from aexpy.preprocessing import getDefault
from aexpy.producer import ProducerOptions
from aexpy.reporting import Reporter as Base


class Evaluator(RuleEvaluator):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "pycompat"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[EvalRule] | None" = None) -> None:
        rules = rules or []

        from aexpy.evaluating import evals
        from aexpy.evaluating.checkers import rankAt

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
