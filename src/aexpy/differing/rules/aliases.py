from aexpy.models import ApiDescription
from aexpy.models.description import CollectionEntry
from ..checkers import DiffRule, DiffRuleCollection, RuleCheckResult, diffrule, fortype

AliasRules = DiffRuleCollection()


@AliasRules.rule
@fortype(CollectionEntry)
@diffrule
def AddAlias(a: CollectionEntry, b: CollectionEntry, **kwargs):
    sub = b.aliasMembers.keys() - a.aliasMembers.keys()
    if len(sub) > 0:
        items = [f"{name}->{b.members[name]}" for name in sub]
        return RuleCheckResult(True, f"Add aliases: {', '.join(items)}", {"changes": {name: b.members[name] for name in sub}})
    return False


@AliasRules.rule
@fortype(CollectionEntry)
@diffrule
def RemoveAlias(a: CollectionEntry, b: CollectionEntry, **kwargs):
    sub = a.aliasMembers.keys() - b.aliasMembers.keys()
    if len(sub) > 0:
        items = [f"{name}->{a.members[name]}" for name in sub]
        return RuleCheckResult(True, f"Remove aliases: {', '.join(items)}", {"changes": {name: a.members[name] for name in sub}})
    return False


@AliasRules.rule
@fortype(CollectionEntry)
@diffrule
def ChangeAlias(a: CollectionEntry, b: CollectionEntry, **kwargs):
    inter = a.members.keys() & b.members.keys()
    changed = {}
    for k in inter:
        if a.members[k] != b.members[k]:
            changed[k] = (a.members[k], b.members[k])
    if len(changed) > 0:
        items = [
            f"{name}:{changed[name][0]}->{changed[name][1]}" for name in changed]
        return RuleCheckResult(True, f"Change alias targets: {', '.join(items)}", {"changes": changed})
    return False
