import functools
import itertools
from itertools import zip_longest
from typing import Callable, OrderedDict

from ..models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                  CollectionEntry, FunctionEntry, ModuleEntry,
                                  Parameter, ParameterKind, SpecialEntry, SpecialKind)

from .checkers import (DiffRule, DiffRuleCollection,
                       RuleCheckResult, diffrule, fortype)


ParameterRules = DiffRuleCollection()

def matchParameters(a: FunctionEntry, b: FunctionEntry):
    def inner():
        posA = filter(lambda x: x.isPositional(), a.parameters)
        posB = filter(lambda x: x.isPositional(), b.parameters)
        for x, y in zip_longest(posA, posB):
            yield x, y

        kwA = {p.name: p for p in filter(
            lambda x: x.isKeyword(), a.parameters)}
        kwB = {p.name: p for p in filter(
            lambda x: x.isKeyword(), b.parameters)}

        for k, v in kwA.items():
            yield v, kwB.get(k)

        for k, v in kwB.items():
            if k in kwA:
                continue
            yield None, v

        for x, y in zip_longest(
                filter(lambda x: x.kind ==
                       ParameterKind.VarPositional, a.parameters),
                filter(lambda x: x.kind == ParameterKind.VarPositional, b.parameters)):
            yield x, y

        for x, y in zip_longest(
                filter(lambda x: x.kind ==
                       ParameterKind.VarKeyword, a.parameters),
                filter(lambda x: x.kind == ParameterKind.VarKeyword, b.parameters)):
            yield x, y

    done = set()

    for x, y in inner():
        nx = x.name if x else None
        ny = y.name if y else None
        if (nx, ny) in done:
            continue
        done.add((nx, ny))
        yield x, y


def changeParameter(checker: Callable[[Parameter | None, Parameter | None, FunctionEntry, FunctionEntry], RuleCheckResult]):
    @ParameterRules.rule
    @fortype(FunctionEntry)
    @diffrule
    @functools.wraps(checker)
    def wrapper(a: FunctionEntry, b: FunctionEntry):
        results = []
        for x, y in matchParameters(a, b):
            result = checker(x, y, a, b)
            if result:
                results.append(
                    f"{x.name if x else 'None'} & {y.name if y else 'None'}{': ' + result.message if result.message else ''}")
        return RuleCheckResult(len(results) > 0, str(results))

    return wrapper


@changeParameter
def AddRequiredParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is None and b is not None and not b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def RemoveRequiredParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None and not a.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def AddOptionalParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is None and b is not None and b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def RemoveOptionalParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None and a.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def ReorderParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and \
            a.isPositional() and b.isPositional() and \
            a.name != b.name:
        if b.name in [p.name for p in old.parameters] and a.name in [p.name for p in new.parameters]:
            return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def AddParameterDefault(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and not a.optional and b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def RemoveParameterDefault(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.optional and not b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def ChangeParameterDefault(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.optional and b.optional and a.default != b.default:
        return RuleCheckResult(True, f"{a.default} -> {b.default}")
    return RuleCheckResult.unsatisfied()


@changeParameter
def RemoveVarPositional(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None and a.kind == ParameterKind.VarPositional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def RemoveVarKeyword(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None and a.kind == ParameterKind.VarKeyword:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()
