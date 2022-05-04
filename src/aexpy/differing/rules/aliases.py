from aexpy.extracting.main.base import islocal
from aexpy.models import ApiDescription
from aexpy.models.description import CollectionEntry
from aexpy.models.difference import DiffEntry

from ..checkers import DiffRule, DiffRuleCollection, diffrule, fortype

AliasRules = DiffRuleCollection()


@AliasRules.rule
@fortype(CollectionEntry)
@diffrule
def AddAlias(a: CollectionEntry, b: CollectionEntry, old: "ApiDescription", new: "ApiDescription"):
    sub = (b.members.keys() - a.members.keys()) & b.aliasMembers.keys()
    return [DiffEntry(message=f"Add alias ({a.id}): {name} => {b.members[name]}", data={"name": name, "target": b.members[name]}) for name in sub]


@AliasRules.rule
@fortype(CollectionEntry)
@diffrule
def RemoveAlias(a: CollectionEntry, b: CollectionEntry, old: "ApiDescription", new: "ApiDescription"):
    sub = (a.members.keys() - b.members.keys()) & a.aliasMembers.keys()
    return [DiffEntry(message=f"Remove alias ({a.id}): {name} => {a.members[name]}", data={"name": name, "target": a.members[name]}) for name in sub if new.resolveName(f"{a.id}.{name}") is None]


@AliasRules.rule
@fortype(CollectionEntry)
@diffrule
def ChangeAlias(a: CollectionEntry, b: CollectionEntry, old: "ApiDescription", new: "ApiDescription"):
    inter = a.members.keys() & b.members.keys()
    changed = {}
    for k in inter:
        if a.members[k] != b.members[k]:
            changed[k] = (a.members[k], b.members[k])
    return [DiffEntry(message=f"Change alias ({a.id}): {name}: {old} => {new}", data={"name": name, "old": old, "new": new}) for name, (old, new) in changed.items()]
