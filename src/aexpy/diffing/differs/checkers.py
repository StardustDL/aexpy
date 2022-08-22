
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable

from aexpy.models.description import ApiEntry
from aexpy.models.difference import BreakingRank

from aexpy.models import ApiDescription, DiffEntry


class DiffConstraint:
    """
    A contraint (checker) generating DiffEntry.

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
class DiffConstraintCollection:
    """Collection of DiffConstraint."""

    constraints: "list[DiffConstraint]" = field(default_factory=list)

    def cons(self, constraint: "DiffConstraint"):
        self.constraints.append(constraint)
        return constraint


def diffcons(checker: "Callable[[ApiEntry, ApiEntry, ApiDescription, ApiDescription], list[DiffEntry]]") -> "DiffConstraint":
    """Create a DiffConstraint on a function."""

    return DiffConstraint(checker.__name__, checker)


def fortype(type, optional: "bool" = False):
    """Limit the diff constraint to a type of ApiEntry."""

    def decorator(constraint: "DiffConstraint") -> "DiffConstraint":
        return constraint.fortype(type, optional)

    return decorator
