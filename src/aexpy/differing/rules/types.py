from aexpy.models.description import AttributeEntry, FunctionEntry, Parameter
from aexpy.models.difference import DiffEntry
from ..checkers import DiffRule, DiffRuleCollection, fortype, diffrule
from .parameters import changeParameter

TypeRules = DiffRuleCollection()


@TypeRules.rule
@fortype(AttributeEntry)
@diffrule
def ChangeAttributeType(a: AttributeEntry, b: AttributeEntry, **kwargs):
    if a.type is not None and b.type is not None and a.type.type != b.type.type:
        return [DiffEntry(message=f"Change attribute type ({a.id}): {a.type.type} -> {b.type.type}.")]
    return []


@TypeRules.rule
@fortype(FunctionEntry)
@diffrule
def ChangeReturnType(a: FunctionEntry, b: FunctionEntry):
    if a.returnType is not None and b.returnType is not None and a.returnType.type != b.returnType.type:
        return [DiffEntry(message=f"Change return type ({a.id}): {a.returnType.type} -> {b.returnType.type}.")]
    return []


@TypeRules.rule
@changeParameter
def ChangeParameterType(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a.type is not None and b.type is not None and a.type.type != b.type.type:
        return [DiffEntry(message=f"Change parameter type ({old.id}): {a.name}({b.name}): {a.type.type} -> {b.type.type}.")]
    return []
