from dataclasses import dataclass, field
from typing import Callable, Iterable, Literal, Type, cast, overload

from ...models import ApiDescription, DiffEntry
from ...models.description import ApiEntry

type T_Checker = Callable[
    [ApiEntry | None, ApiEntry | None, ApiDescription, ApiDescription],
    Iterable[DiffEntry],
]


class DiffConstraint:
    """
    A contraint (checker) generating DiffEntry.

    checker: def checker(a: ApiEntry | None, b: ApiEntry | None, old=oldApiDescription, new=newApiDescription) -> RuleCheckResult | bool: pass
    """

    def __init__(
        self,
        /,
        kind: str = "",
        checker: T_Checker | None = None,
    ) -> None:
        self.checker = (
            checker if checker else cast(T_Checker, lambda a, b, old, new: [])
        )
        self.kind = kind

    def askind(self, /, kind: str):
        """Set kind."""

        self.kind = kind
        return self

    def fortype(self, /, type: Type, optional: bool = False):
        """Limit to a type of ApiEntry."""

        oldchecker = self.checker

        def checker(a, b, old, new) -> Iterable[DiffEntry]:
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
        /,
        old: ApiEntry | None,
        new: ApiEntry | None,
        oldCollection: ApiDescription,
        newCollection: ApiDescription,
    ) -> Iterable[DiffEntry]:
        result = self.checker(old, new, oldCollection, newCollection)
        return (
            (
                entry.model_copy(update={"kind": self.kind, "old": old, "new": new})
                for entry in result
            )
            if result
            else []
        )


@dataclass
class DiffConstraintCollection:
    """Collection of DiffConstraint."""

    constraints: list[DiffConstraint] = field(default_factory=list)

    def cons(self, /, constraint: DiffConstraint):
        self.constraints.append(constraint)
        return constraint


def diffcons(
    checker: T_Checker,
) -> DiffConstraint:
    """Create a DiffConstraint on a function."""

    return DiffConstraint(checker.__name__, checker)


@overload
def typedCons[
    TEntry: ApiEntry
](type: type[TEntry], optional: Literal[False] = False) -> Callable[
    [Callable[[TEntry, TEntry, ApiDescription, ApiDescription], Iterable[DiffEntry]]],
    DiffConstraint,
]: ...


@overload
def typedCons[
    TEntry: ApiEntry
](type: type[TEntry], optional: Literal[True]) -> Callable[
    [
        Callable[
            [TEntry | None, TEntry | None, ApiDescription, ApiDescription],
            Iterable[DiffEntry],
        ]
    ],
    DiffConstraint,
]: ...


def typedCons[
    TEntry: ApiEntry
](type: type[TEntry], optional: Literal[True, False] = False):
    """Limit the diff constraint to a type of ApiEntry."""

    if optional:

        def op(
            checker: Callable[
                [TEntry | None, TEntry | None, ApiDescription, ApiDescription],
                Iterable[DiffEntry],
            ],
            /,
        ):
            return DiffConstraint(checker.__name__, cast(T_Checker, checker)).fortype(
                type, True
            )

        return op
    else:

        def nonop(
            checker: Callable[
                [TEntry, TEntry, ApiDescription, ApiDescription], Iterable[DiffEntry]
            ],
            /,
        ):
            return DiffConstraint(checker.__name__, cast(T_Checker, checker)).fortype(
                type, optional
            )

        return nonop
