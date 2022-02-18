
from dataclasses import dataclass, field
from typing import Any, Callable

from aexpy.models.difference import BreakingRank

from ..models import DiffEntry


@dataclass
class RuleCheckResult:
    """Result for a diff rule."""

    result: "bool" = False
    """Result."""

    message: "str" = ""
    """Message, used by DiffEntry."""

    data: "dict[str, Any]" = field(default_factory=dict)
    """Data, used by DiffEntry."""

    @classmethod
    def satisfied(cls) -> "RuleCheckResult":
        if not hasattr(cls, "_satisfied"):
            cls._satisfied = RuleCheckResult(True)
        return cls._satisfied

    @classmethod
    def unsatisfied(cls) -> "RuleCheckResult":
        if not hasattr(cls, "_unsatisfied"):
            cls._unsatisfied = RuleCheckResult(False)
        return cls._unsatisfied

    def __bool__(self):
        return self.result

    def __and__(self, other: "RuleCheckResult"):
        return RuleCheckResult(self.result and other.result, f"({self.message} && {other.message})")

    def __or__(self, other: "RuleCheckResult"):
        return RuleCheckResult(self.result or other.result, f"({self.message} || {other.message})")

    def __invert__(self):
        return RuleCheckResult(not self.result, f"!{self.message}")


def toRuleCheckResult(value: "RuleCheckResult | bool"):
    match value:
        case RuleCheckResult():
            return value
        case True:
            return RuleCheckResult.satisfied()
        case False:
            return RuleCheckResult.unsatisfied()


class DiffRule:
    """
    A rule (checker) generating DiffEntry.

    checker: def checker(a: ApiEntry | None, b: ApiEntry | None, old=oldApiDescription, new=newApiDescription) -> RuleCheckResult | bool: pass
    """

    def __init__(self, kind: "str" = "", checker: "Callable[..., RuleCheckResult | bool] | None" = None) -> None:
        if checker is None:
            def checker(a, b, **kwargs):
                return RuleCheckResult.unsatisfied()
        self.checker: "Callable[..., RuleCheckResult]" = checker
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
                if a is None or isinstance(a, type):
                    if b is None or isinstance(b, type):
                        return oldchecker(a, b, **kwargs)
                return RuleCheckResult.unsatisfied()
            else:
                if isinstance(a, type) and isinstance(b, type):
                    return oldchecker(a, b, **kwargs)
                else:
                    return RuleCheckResult.unsatisfied()

        self.checker = checker
        return self

    def __call__(self, old, new, oldCollection, newCollection) -> Any:
        result = toRuleCheckResult(self.checker(
            old, new, old=oldCollection, new=newCollection))
        if result:
            return DiffEntry(kind=self.kind, message=result.message, data=result.data, old=old, new=new)

    def __and__(self, other: "DiffRule"):
        def checker(a, b, **kwargs):
            return self.checker(a, b, **kwargs) & other.checker(a, b, **kwargs)
        return DiffRule(f"({self.kind} & {other.kind})", checker)

    def __or__(self, other: "DiffRule"):
        def checker(a, b, **kwargs):
            return self.checker(a, b, **kwargs) | other.checker(a, b, **kwargs)
        return DiffRule(f"({self.kind} | {other.kind})", checker)

    def __invert__(self):
        return DiffRule(f"!{self.kind}", lambda a, b: ~self.checker(a, b))


@dataclass
class DiffRuleCollection:
    """Collection of DiffRule."""

    rules: "list[DiffRule]" = field(default_factory=list)

    def rule(self, rule: "DiffRule"):
        self.rules.append(rule)
        return rule


def diffrule(checker: "Callable[..., RuleCheckResult | bool]") -> "DiffRule":
    """Create a DiffRule on a function."""

    return DiffRule(checker.__name__, checker)


def fortype(type, optional: "bool" = False):
    """Limit the diff rule to a type of ApiEntry."""

    def decorator(rule: "DiffRule") -> "DiffRule":
        return rule.fortype(type, optional)

    return decorator
