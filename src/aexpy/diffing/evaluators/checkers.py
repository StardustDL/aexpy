from dataclasses import dataclass, field
from typing import Callable, cast

from ...models import ApiDescription, ApiDifference, DiffEntry
from ...models.difference import BreakingRank

T_Checker = Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], None]


class EvalRule:
    """
    A rule (evaluator) generating DiffEntry(s).

    checker: def checker(entry, difference) -> list[DiffEntry]: pass
    """

    def __init__(
        self,
        /,
        kind: str = "",
        checker: T_Checker | None = None,
    ) -> None:
        self.checker = (
            checker if checker else cast(T_Checker, lambda e, d, old, new: None)
        )
        self.kind = kind

    def forkind(self, /, kind: str):
        """Set kind."""

        self.kind = kind
        return self

    def __call__(
        self,
        /,
        entry: DiffEntry,
        diff: ApiDifference,
        old: ApiDescription,
        new: ApiDescription,
    ):
        if self.kind and entry.kind != self.kind:
            return
        return self.checker(entry, diff, old, new)


@dataclass
class EvalRuleCollection:
    """Collection for rule evaluators."""

    rules: list[EvalRule] = field(default_factory=list)

    def rule(self, /, rule: EvalRule):
        self.rules.append(rule)
        return rule


def evalrule(
    checker: T_Checker,
) -> EvalRule:
    """Create a rule evaluator on a function."""

    return EvalRule(checker.__name__, checker)


def forallkinds(rule: EvalRule) -> EvalRule:
    """Create a rule evaluator for all kinds of DiffEntry."""

    return rule.forkind("")


def forkind(kind: str):
    """Create a rule evaluator for a kind of DiffEntry."""

    def decorator(rule: EvalRule) -> EvalRule:
        return rule.forkind(kind)

    return decorator


def rankAt(kind: str, rank: BreakingRank, privateRank: BreakingRank | None = None):
    """Create a rule evaluator that ranks a kind of DiffEntry."""

    def checker(
        entry: DiffEntry,
        diff: ApiDifference,
        old: ApiDescription,
        new: ApiDescription,
    ):
        eold = entry.old
        enew = entry.new
        if (eold and eold.private) or (enew and enew.private):
            entry.rank = privateRank if privateRank is not None else rank
        else:
            entry.rank = rank

    return EvalRule(kind, checker)
