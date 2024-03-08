from ....models import ApiDescription
from ....models.description import AttributeEntry, FunctionEntry, Parameter
from ....models.difference import DiffEntry
from ....models.typing import AnyType
from ..checkers import (DiffConstraint, DiffConstraintCollection, diffcons,
                        typedCons)
from .parameters import changeParameter

TypeConstraints = DiffConstraintCollection()


@TypeConstraints.cons
@typedCons(AttributeEntry)
def ChangeAttributeType(
    a: AttributeEntry, b: AttributeEntry, old: "ApiDescription", new: "ApiDescription"
):
    if a.type is not None and b.type is not None and a.type.id != b.type.id:
        if isinstance(a.type, AnyType) and a.annotation == "":
            return
        if isinstance(b.type, AnyType) and b.annotation == "":
            return
        yield DiffEntry(
            message=f"Change attribute type ({a.id}): {a.type.id} => {b.type.id}",
            data={"oldtype": a.type.id, "newtype": b.type.id},
        )
    return


@TypeConstraints.cons
@typedCons(FunctionEntry)
def ChangeReturnType(
    a: FunctionEntry, b: FunctionEntry, old: "ApiDescription", new: "ApiDescription"
):
    if (
        a.returnType is not None
        and b.returnType is not None
        and a.returnType.id != b.returnType.id
    ):
        if isinstance(a.returnType, AnyType) and a.returnAnnotation == "":
            return
        if isinstance(b.returnType, AnyType) and b.returnAnnotation == "":
            return
        yield DiffEntry(
            message=f"Change return type ({a.id}): {a.returnType.id} => {b.returnType.id}",
            data={"oldtype": a.returnType.id, "newtype": b.returnType.id},
        )


@TypeConstraints.cons
@changeParameter
def ChangeParameterType(
    a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry
):
    if a is not None and b is not None:
        if a.name == b.name:
            if a.type is not None and b.type is not None and a.type.id != b.type.id:
                if isinstance(a.type, AnyType) and a.annotation == "":
                    return
                if isinstance(b.type, AnyType) and b.annotation == "":
                    return
                yield DiffEntry(
                    message=f"Change parameter type ({old.id}): {a.name}: {a.type.id} => {b.type.id}",
                    data={"oldtype": a.type.id, "newtype": b.type.id},
                )
