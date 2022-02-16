
from dataclasses import dataclass, field
from typing import Any, Callable

from ..models import DiffEntry, ApiDifference


class RuleEvaluator:
    """
    checker: def checker(entry, difference): pass
    """

    def __init__(self, kind: "str" = "", checker: "Callable[[DiffEntry, ApiDifference], list[DiffEntry]] | None" = None) -> None:
        if checker is None:
            def checker(a, b):
                return []
        self.checker: "Callable[[DiffEntry, ApiDifference], list[DiffEntry]]" = checker
        self.kind = kind

    def forkind(self, kind: "str"):
        self.kind = kind
        return self

    def __call__(self, entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
        if self.kind and entry.kind != self.kind:
            return []
        return self.checker(entry, diff)


@dataclass
class RuleEvaluatorCollection:
    ruleevals: "list[RuleEvaluator]" = field(default_factory=list)

    def ruleeval(self, ruleeval: "RuleEvaluator"):
        self.ruleevals.append(ruleeval)
        return ruleeval


def ruleeval(checker: "Callable[[DiffEntry, ApiDifference], list[DiffEntry]]") -> "RuleEvaluator":
    return RuleEvaluator(checker.__name__, checker)


def forallkinds(rule: "RuleEvaluator") -> "RuleEvaluator":
    return rule.forkind("")


def forkind(kind: str):
    def decorator(rule: "RuleEvaluator") -> "RuleEvaluator":
        return rule.forkind(kind)

    return decorator
