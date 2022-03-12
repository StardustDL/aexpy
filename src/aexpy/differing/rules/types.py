from aexpy.models.description import AttributeEntry, FunctionEntry, Parameter
from aexpy.models.difference import DiffEntry

from ..checkers import DiffRule, DiffRuleCollection, diffrule, fortype
from .parameters import changeParameter

TypeRules = DiffRuleCollection()


@TypeRules.rule
@fortype(AttributeEntry)
@diffrule
def ChangeAttributeType(a: AttributeEntry, b: AttributeEntry, **kwargs):
    if a.type is not None and b.type is not None and a.type.id != b.type.id:
        return [DiffEntry(message=f"Change attribute type ({a.id}): {a.type.id} -> {b.type.id}", data={"oldtype": a.type.id, "newtype": b.type.id})]
    return []


@TypeRules.rule
@fortype(FunctionEntry)
@diffrule
def ChangeReturnType(a: FunctionEntry, b: FunctionEntry, **kwargs):
    if a.returnType is not None and b.returnType is not None and a.returnType.id != b.returnType.id:
        return [DiffEntry(message=f"Change return type ({a.id}): {a.returnType.id} -> {b.returnType.id}", data={"oldtype": a.returnType.id, "newtype": b.returnType.id})]
    return []


@TypeRules.rule
@changeParameter
def ChangeParameterType(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None:
        if a.type is not None and b.type is not None and a.type.id != b.type.id:
            return [DiffEntry(message=f"Change parameter type ({old.id}): {a.name}({b.name}): {a.type.id} -> {b.type.id}", data={"oldtype": a.type.id, "newtype": b.type.id})]
    return []
