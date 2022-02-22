from aexpy.models.description import ApiEntry, SpecialEntry, SpecialKind
from aexpy.models.difference import DiffEntry

from ..checkers import DiffRule, DiffRuleCollection, diffrule, fortype

ExternalRules = DiffRuleCollection()


@ExternalRules.rule
@fortype(SpecialEntry, True)
@diffrule
def AddExternal(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if a is None and b is not None:
        if b.kind == SpecialKind.External:
            return [DiffEntry(message=f"Add external: {b.id}.")]
    return []


@ExternalRules.rule
@fortype(SpecialEntry, True)
@diffrule
def RemoveExternal(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if b is None and a is not None:
        if a.kind == SpecialKind.External:
            return [DiffEntry(message=f"Remove external: {a.id}.")]
    return []
