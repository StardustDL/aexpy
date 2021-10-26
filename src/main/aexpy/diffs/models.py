from dataclasses import dataclass, field
from typing import Any, Callable

from ..analyses.models import ApiEntry, ApiManifest


@dataclass
class RuleCheckResult:
    result: bool = False
    message: str = ""

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


class DiffRule:
    def __init__(self, kind: str = "", checker: Callable[[Any, Any], RuleCheckResult] | None = None) -> None:
        self.checker: Callable[[Any, Any], RuleCheckResult] = checker or (
            lambda a, b: RuleCheckResult.unsatisfied())
        self.kind = kind

    def askind(self, kind: str):
        self.kind = kind
        return self

    def fortype(self, type, optional: bool = False):
        oldchecker = self.checker
        if optional:
            self.checker = lambda a, b: oldchecker(a, b) if \
                (a is None or isinstance(a, type)) and (b is None or isinstance(b, type)) else RuleCheckResult.unsatisfied()
        else:
            self.checker = lambda a, b: oldchecker(a, b) if \
                isinstance(a, type) and isinstance(b, type) else RuleCheckResult.unsatisfied()
        return self

    def __call__(self, old, new) -> Any:
        result = self.checker(old, new)
        if result:
            oldId = old.id if old else "None"
            newId = new.id if new else "None"
            return DiffEntry(kind=self.kind, message=f"{oldId} & {newId}: {result.message}", old=old, new=new)

    def __and__(self, other: "DiffRule"):
        return DiffRule(f"({self.kind} & {other.kind})", lambda a, b: self.checker(a, b) & other.checker(a, b))

    def __or__(self, other: "DiffRule"):
        return DiffRule(f"({self.kind} | {other.kind})", lambda a, b: self.checker(a, b) | other.checker(a, b))

    def __invert__(self):
        return DiffRule(f"!{self.kind}", lambda a, b: ~self.checker(a, b))


@dataclass
class DiffEntry:
    id: str = ""
    kind: str = ""
    message: str = ""
    old: ApiEntry | None = field(default=None, repr=False)
    new: ApiEntry | None = field(default=None, repr=False)


@dataclass
class DiffCollection:
    old: ApiManifest = field(default_factory=ApiManifest)
    new: ApiManifest = field(default_factory=ApiManifest)
    entries: dict[str, ApiEntry] = field(default_factory=dict)

    def kind(self, name: str):
        return list(filter(lambda x: x.kind == name, self.entries.values()))
