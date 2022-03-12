
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable

from aexpy.models.difference import BreakingRank

from ..models import ApiDescription, ApiDifference, DiffEntry


class EvalRule:
    """
    A rule (evaluator) generating DiffEntry(s).

    checker: def checker(entry, difference) -> list[DiffEntry]: pass
    """

    def __init__(self, kind: "str" = "", checker: "Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], None] | None" = None) -> None:
        if checker is None:
            def checker(a, b, old, new):
                pass
        self.checker: "Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], None]" = checker
        self.kind = kind

    def forkind(self, kind: "str"):
        """Set kind."""

        self.kind = kind
        return self

    def __call__(self, entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
        if self.kind and entry.kind != self.kind:
            return
        return self.checker(entry, diff, old, new)


@dataclass
class EvalRuleCollection:
    """Collection for rule evaluators."""

    ruleevals: "list[EvalRule]" = field(default_factory=list)

    def ruleeval(self, ruleeval: "EvalRule"):
        self.ruleevals.append(ruleeval)
        return ruleeval


def ruleeval(checker: "Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], None]") -> "EvalRule":
    """Create a rule evaluator on a function."""

    return EvalRule(checker.__name__, checker)


def forallkinds(rule: "EvalRule") -> "EvalRule":
    """Create a rule evaluator for all kinds of DiffEntry."""

    return rule.forkind("")


def forkind(kind: str):
    """Create a rule evaluator for a kind of DiffEntry."""

    def decorator(rule: "EvalRule") -> "EvalRule":
        return rule.forkind(kind)

    return decorator


def rankAt(kind: str, rank: "BreakingRank", privateRank: "BreakingRank | None" = None):
    """Create a rule evaluator that ranks a kind of DiffEntry."""

    def checker(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
        eold = entry.old
        enew = entry.new
        if (eold and eold.private) or (enew and enew.private):
            entry.rank = privateRank if privateRank is not None else rank
        else:
            entry.rank = rank

    return EvalRule(kind, checker)
