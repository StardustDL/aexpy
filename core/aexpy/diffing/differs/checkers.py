import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, Type, cast

from aexpy.models.description import ApiEntry
from aexpy.models.difference import BreakingRank

from aexpy.models import ApiDescription, DiffEntry

T_Checker = Callable[
    [ApiEntry | None, ApiEntry | None, ApiDescription, ApiDescription], list[DiffEntry]
]


class DiffConstraint:
    """
    A contraint (checker) generating DiffEntry.

    checker: def checker(a: ApiEntry | None, b: ApiEntry | None, old=oldApiDescription, new=newApiDescription) -> RuleCheckResult | bool: pass
    """

    def __init__(
        self,
        kind: str = "",
        checker: T_Checker | None = None,
    ) -> None:
        self.checker = (
            checker if checker else cast(T_Checker, lambda a, b, old, new: [])
        )
        self.kind = kind

    def askind(self, kind: str):
        """Set kind."""

        self.kind = kind
        return self

    def fortype(self, type: Type, optional: bool = False):
        """Limit to a type of ApiEntry."""

        oldchecker = self.checker

        def checker(a, b, old, new) -> list[DiffEntry]:
            if optional:
                if not isinstance(a, type):
                    a = None
                if not isinstance(b, type):
                    b = None
                if a or b:
                    return oldchecker(a, b, old, new)
            else:
                if isinstance(a, type) and isinstance(b, type):
                    return oldchecker(a, b, old, new)
            return []

        self.checker = cast(T_Checker, checker)
        return self

    def __call__(
        self,
        old: ApiEntry | None,
        new: ApiEntry | None,
        oldCollection: ApiDescription,
        newCollection: ApiDescription,
    ) -> list[DiffEntry]:
        result = self.checker(old, new, oldCollection, newCollection)
        return (
            [
                dataclasses.replace(entry, kind=self.kind, old=old, new=new)
                for entry in result
            ]
            if result
            else []
        )


@dataclass
class DiffConstraintCollection:
    """Collection of DiffConstraint."""

    constraints: list[DiffConstraint] = field(default_factory=list)

    def cons(self, constraint: DiffConstraint):
        self.constraints.append(constraint)
        return constraint


def diffcons(
    checker: T_Checker,
) -> DiffConstraint:
    """Create a DiffConstraint on a function."""

    return DiffConstraint(checker.__name__, checker)  # type: ignore


def fortype(type, optional: bool = False):
    """Limit the diff constraint to a type of ApiEntry."""

    def decorator(constraint: DiffConstraint) -> DiffConstraint:
        return constraint.fortype(type, optional)

    return decorator
