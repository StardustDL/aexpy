from aexpy.models.description import SpecialEntry, ApiEntry, SpecialKind
from ..checkers import DiffRule, DiffRuleCollection, RuleCheckResult, diffrule, fortype


ExternalRules = DiffRuleCollection()


@ExternalRules.rule
@fortype(SpecialEntry, True)
@diffrule
def AddExternal(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if a is None and b is not None:
        if b.kind == SpecialKind.External:
            return RuleCheckResult(True, f"Add external: {b.id}.")
    return False


@ExternalRules.rule
@fortype(SpecialEntry, True)
@diffrule
def RemoveExternal(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if b is None and a is not None:
        if a.kind == SpecialKind.External:
            return RuleCheckResult(True, f"Remove external: {a.id}.")
    return False
