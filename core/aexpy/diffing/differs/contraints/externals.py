from aexpy.models import ApiDescription
from aexpy.models.description import ApiEntry, SpecialEntry, SpecialKind
from aexpy.models.difference import DiffEntry

from ..checkers import DiffConstraint, DiffConstraintCollection, typedConsOp

ExternalConstraints = DiffConstraintCollection()


@ExternalConstraints.cons
@typedConsOp(SpecialEntry)
def AddExternal(
    a: SpecialEntry | None,
    b: SpecialEntry | None,
    old: "ApiDescription",
    new: "ApiDescription",
):
    if a is None and b is not None:
        if b.kind == SpecialKind.External:
            return [DiffEntry(message=f"Add external: {b.id}.")]
    return []


@ExternalConstraints.cons
@typedConsOp(SpecialEntry)
def RemoveExternal(
    a: SpecialEntry | None,
    b: SpecialEntry | None,
    old: "ApiDescription",
    new: "ApiDescription",
):
    if b is None and a is not None:
        if a.kind == SpecialKind.External:
            return [DiffEntry(message=f"Remove external: {a.id}.")]
    return []
