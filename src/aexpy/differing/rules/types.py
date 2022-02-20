from aexpy.models.description import AttributeEntry, FunctionEntry, Parameter
from ..checkers import DiffRule, DiffRuleCollection, fortype, diffrule
from .parameters import changeParameter

TypeRules = DiffRuleCollection()


@TypeRules.rule
@fortype(AttributeEntry)
@diffrule
def ChangeAttributeType(a: AttributeEntry, b: AttributeEntry, **kwargs):
    if a.type != b.type:
        return RuleCheckResult(True, f"{a.type} -> {b.type}")
    return RuleCheckResult.unsatisfied()


@TypeRules.rule
@fortype(FunctionEntry)
@diffrule
def ChangeReturnType(a: FunctionEntry, b: FunctionEntry):
    if a.returnType != b.returnType:
        return RuleCheckResult(True, f"{a.returnType} -> {b.returnType}")
    return RuleCheckResult.unsatisfied()


@TypeRules.rule
@changeParameter
def ChangeParameterType(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.type != b.type:
        return RuleCheckResult(True, f"{a.type} -> {b.type}")
    return RuleCheckResult.unsatisfied()
