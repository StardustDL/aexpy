
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable

from aexpy.models.description import ApiEntry
from aexpy.models.difference import BreakingRank

from ..models import ApiDescription, DiffEntry


class DiffRule:
    """
    A rule (checker) generating DiffEntry.

    checker: def checker(a: ApiEntry | None, b: ApiEntry | None, old=oldApiDescription, new=newApiDescription) -> RuleCheckResult | bool: pass
    """

    def __init__(self, kind: "str" = "", checker: "Callable[[ApiEntry | None, ApiEntry | None, ApiDescription, ApiDescription], list[DiffEntry]] | None" = None) -> None:
        if checker is None:
            def checker(a, b, old, new):
                return []
        self.checker: "Callable[[ApiEntry | None, ApiEntry | None, ApiDescription, ApiDescription], list[DiffEntry]]" = checker
        self.kind = kind

    def askind(self, kind: "str"):
        """Set kind."""

        self.kind = kind
        return self

    def fortype(self, type, optional: bool = False):
        """Limit to a type of ApiEntry."""

        oldchecker = self.checker

        def checker(a, b, **kwargs):
            if optional:
                if not isinstance(a, type):
                    a = None
                if not isinstance(b, type):
                    b = None
                if a or b:
                    return oldchecker(a, b, **kwargs)
                return []
            else:
                if isinstance(a, type) and isinstance(b, type):
                    return oldchecker(a, b, **kwargs)
                else:
                    return []

        self.checker = checker
        return self

    def __call__(self, old, new, oldCollection, newCollection) -> "list[DiffEntry]":
        result = self.checker(
            old, new, old=oldCollection, new=newCollection)
        if result:
            return [dataclasses.replace(entry, kind=self.kind, old=old, new=new) for entry in result]


@dataclass
class DiffRuleCollection:
    """Collection of DiffRule."""

    rules: "list[DiffRule]" = field(default_factory=list)

    def rule(self, rule: "DiffRule"):
        self.rules.append(rule)
        return rule


def diffrule(checker: "Callable[[ApiEntry, ApiEntry, ApiDescription, ApiDescription], list[DiffEntry]]") -> "DiffRule":
    """Create a DiffRule on a function."""

    return DiffRule(checker.__name__, checker)


def fortype(type, optional: "bool" = False):
    """Limit the diff rule to a type of ApiEntry."""

    def decorator(rule: "DiffRule") -> "DiffRule":
        return rule.fortype(type, optional)

    return decorator
