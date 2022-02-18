
from dataclasses import dataclass, field
import dataclasses
from typing import Any, Callable

from aexpy.models.difference import BreakingRank

from ..models import DiffEntry, ApiDifference


class RuleEvaluator:
    """
    A rule (evaluator) generating DiffEntry(s).

    checker: def checker(entry, difference) -> list[DiffEntry]: pass
    """

    def __init__(self, kind: "str" = "", checker: "Callable[[DiffEntry, ApiDifference], list[DiffEntry]] | None" = None) -> None:
        if checker is None:
            def checker(a, b):
                return []
        self.checker: "Callable[[DiffEntry, ApiDifference], list[DiffEntry]]" = checker
        self.kind = kind

    def forkind(self, kind: "str"):
        """Set kind."""

        self.kind = kind
        return self

    def __call__(self, entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
        if self.kind and entry.kind != self.kind:
            return []
        return self.checker(entry, diff)


@dataclass
class RuleEvaluatorCollection:
    """Collection for rule evaluators."""

    ruleevals: "list[RuleEvaluator]" = field(default_factory=list)

    def ruleeval(self, ruleeval: "RuleEvaluator"):
        self.ruleevals.append(ruleeval)
        return ruleeval


def ruleeval(checker: "Callable[[DiffEntry, ApiDifference], list[DiffEntry]]") -> "RuleEvaluator":
    """Create a rule evaluator on a function."""

    return RuleEvaluator(checker.__name__, checker)


def forallkinds(rule: "RuleEvaluator") -> "RuleEvaluator":
    """Create a rule evaluator for all kinds of DiffEntry."""

    return rule.forkind("")


def forkind(kind: str):
    """Create a rule evaluator for a kind of DiffEntry."""

    def decorator(rule: "RuleEvaluator") -> "RuleEvaluator":
        return rule.forkind(kind)

    return decorator


def rankAt(kind: str, rank: "BreakingRank"):
    """Create a rule evaluator that ranks a kind of DiffEntry."""

    def checker(entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
        return [dataclasses.replace(entry, rank=rank)]

    return RuleEvaluator(kind, checker)
