from ....models import ApiDescription
from ....models.description import ApiEntry, SpecialEntry, SpecialKind
from ....models.difference import DiffEntry
from ..checkers import DiffConstraint, DiffConstraintCollection, typedCons

ExternalConstraints = DiffConstraintCollection()


@ExternalConstraints.cons
@typedCons(SpecialEntry, True)
def AddExternal(
    a: SpecialEntry | None,
    b: SpecialEntry | None,
    old: "ApiDescription",
    new: "ApiDescription",
):
    if a is None and b is not None:
        if b.kind == SpecialKind.External:
            yield DiffEntry(message=f"Add external: {b.id}.")


@ExternalConstraints.cons
@typedCons(SpecialEntry, True)
def RemoveExternal(
    a: SpecialEntry | None,
    b: SpecialEntry | None,
    old: "ApiDescription",
    new: "ApiDescription",
):
    if b is None and a is not None:
        if a.kind == SpecialKind.External:
            yield DiffEntry(message=f"Remove external: {a.id}.")
