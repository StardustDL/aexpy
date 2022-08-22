import subprocess
import functools
from pathlib import Path
from socket import timeout
from typing import Callable
from .. import Differ
from ..evaluators.checkers import EvalRule, EvalRuleCollection, evalrule
from ..evaluators.default import RuleEvaluator
from aexpy.models import ApiDifference, ApiDescription, Distribution
from aexpy.models.difference import BreakingRank, DiffEntry, VerifyState


def trigger(generator: "Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], list[str]]") -> "EvalRule":
    @functools.wraps(generator)
    def wrapper(entry: DiffEntry, diff: ApiDifference, old: ApiDescription, new: ApiDescription) -> None:
        if entry.rank == BreakingRank.Compatible or entry.rank == BreakingRank.Unknown:
            return
        tri = generator(entry, diff, old, new)
        if tri:
            entry.data["verify"] = {"trigger": tri}

    return evalrule(wrapper)
