from ....models import ApiDescription
from ....models.description import ClassEntry
from ....models.difference import DiffEntry
from ....utils import getObjectId
from ..checkers import (DiffConstraint, DiffConstraintCollection, diffcons,
                        typedCons)
from . import add, remove

ClassConstraints = DiffConstraintCollection()

AddClass = DiffConstraint("AddClass", add).fortype(ClassEntry, True)
RemoveClass = DiffConstraint("RemoveClass", remove).fortype(ClassEntry, True)

ClassConstraints.cons(AddClass)
ClassConstraints.cons(RemoveClass)


@ClassConstraints.cons
@typedCons(ClassEntry)
def AddBaseClass(
    a: ClassEntry, b: ClassEntry, old: ApiDescription, new: ApiDescription
):
    sa = set(a.bases)
    sb = set(b.bases)
    plus = sb - sa - {getObjectId(object)}

    return (
        DiffEntry(message=f"Add base class ({a.id}): {name}", data={"name": name})
        for name in plus
        if name not in a.mros
    )


@ClassConstraints.cons
@typedCons(ClassEntry)
def RemoveBaseClass(
    a: ClassEntry, b: ClassEntry, old: ApiDescription, new: ApiDescription
):
    sa = set(a.bases)
    sb = set(b.bases)
    minus = sa - sb - {getObjectId(object)}

    return (
        DiffEntry(message=f"Remove base class ({a.id}): {name}", data={"name": name})
        for name in minus
        if name not in b.mros
    )


@ClassConstraints.cons
@typedCons(ClassEntry)
def ImplementAbstractBaseClass(
    a: ClassEntry, b: ClassEntry, old: ApiDescription, new: ApiDescription
):
    sa = set(a.abcs)
    sb = set(b.abcs)
    plus = sb - sa

    return (
        DiffEntry(
            message=f"Implement abstract base class ({a.id}): {name}",
            data={"name": name},
        )
        for name in plus
    )


@ClassConstraints.cons
@typedCons(ClassEntry)
def DeimplementAbstractBaseClass(
    a: ClassEntry, b: ClassEntry, old: ApiDescription, new: ApiDescription
):
    sa = set(a.abcs)
    sb = set(b.abcs)

    minus = sa - sb
    return (
        DiffEntry(
            message=f"Deimplement abstract base class ({a.id}): {name}",
            data={"name": name},
        )
        for name in minus
    )


@ClassConstraints.cons
@typedCons(ClassEntry)
def ChangeMethodResolutionOrder(
    a: ClassEntry, b: ClassEntry, old: ApiDescription, new: ApiDescription
):
    sa = a.mros
    sb = a.mros

    changed = False
    for i in range(len(sa)):
        if changed:
            break
        if i >= len(sb):
            changed = True
        elif sa[i] != sb[i]:
            changed = True

    if changed:
        yield DiffEntry(
            message=f"Change method resolution order ({a.id}): {sa} -> {sb}",
            data={"oldmro": sa, "newmro": sb},
        )
