from aexpy.models.description import ClassEntry
from aexpy.models.difference import DiffEntry
from aexpy.utils import getObjectId

from ..checkers import DiffRule, DiffRuleCollection, diffrule, fortype
from . import add, remove

ClassRules = DiffRuleCollection()

AddClass = DiffRule("AddClass", add).fortype(ClassEntry, True)
RemoveClass = DiffRule("RemoveClass", remove).fortype(ClassEntry, True)

ClassRules.rule(AddClass)
ClassRules.rule(RemoveClass)


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def AddBaseClass(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = set(a.bases)
    sb = set(b.bases)
    plus = sb - sa - {getObjectId(object)}

    return [DiffEntry(message=f"Add base class ({a.id}): {name}", data={"name": name}) for name in plus if name not in a.mro]


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def RemoveBaseClass(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = set(a.bases)
    sb = set(b.bases)
    minus = sa - sb - {getObjectId(object)}

    return [DiffEntry(message=f"Remove base class ({a.id}): {name}", data={"name": name}) for name in minus if name not in b.mro]


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def ImplementAbstractBaseClass(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = set(a.abcs)
    sb = set(b.abcs)
    plus = sb - sa

    return [DiffEntry(message=f"Implement abstract base class ({a.id}): {name}", data={"name": name}) for name in plus]


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def DeimplementAbstractBaseClass(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = set(a.abcs)
    sb = set(b.abcs)

    minus = sa - sb
    return [DiffEntry(message=f"Deimplement abstract base class ({a.id}): {name}", data={"name": name}) for name in minus]


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def ChangeMethodResolutionOrder(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = a.mro
    sb = a.mro

    changed = False
    for i in range(len(sa)):
        if changed:
            break
        if i >= len(sb):
            changed = True
        elif sa[i] != sb[i]:
            changed = True

    if changed:
        return [DiffEntry(message=f"Change method resolution order ({a.id}): {sa} -> {sb}", data={"oldmro": sa, "newmro": sb})]
    return []
