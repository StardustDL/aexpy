import functools
import itertools
from itertools import zip_longest
from typing import Callable, Iterator, OrderedDict

from aexpy.models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                      CollectionEntry, FunctionEntry, ModuleEntry,
                                      Parameter, ParameterKind, SpecialEntry, SpecialKind)

from ..checkers import (DiffRule, DiffRuleCollection,
                        RuleCheckResult, diffrule, fortype)


ParameterRules = DiffRuleCollection()


def matchParameters(a: "FunctionEntry", b: "FunctionEntry"):
    def inner() -> "Iterator[tuple[Parameter | None, Parameter | None]]":
        for x, y in zip_longest(a.positionals, b.positionals):
            yield x, y

        kwA = {v.name: v for v in a.keywords}
        kwB = {v.name: v for v in b.keywords}

        for k, v in kwA.items():
            yield v, kwB.get(k)

        for k, v in kwB.items():
            if k not in kwA:
                yield None, v

        x, y = a.varPositional, b.varPositional
        if x or y:
            yield x, y

        x, y = a.varKeyword, b.varKeyword
        if x or y:
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
    @fortype(FunctionEntry)
    @diffrule
    @functools.wraps(checker)
    def wrapper(a: FunctionEntry, b: FunctionEntry, **kwargs):
        results: "list[tuple[Parameter | None, Parameter | None, RuleCheckResult]]" = [
        ]
        for x, y in matchParameters(a, b):
            result = checker(x, y, a, b)
            if result:
                results.append((x, y, result))
        message = ""
        if results:
            message = ", ".join(result.message for x, y, result in results)
            data = [(x.name if x else "None", y.name if y else "None",
                     result.data) for x, y, result in results]
            return RuleCheckResult(True, message, {"data": data})
        return False

    return wrapper


@ParameterRules.rule
@changeParameter
def AddParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is None and b is not None:
        return RuleCheckResult(True, f"Add parameter {b.name}.")
    return False


@ParameterRules.rule
@changeParameter
def RemoveParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None:
        return RuleCheckResult(True, f"Remove parameter {a.name}.")
    return False


@ParameterRules.rule
@fortype(FunctionEntry)
@diffrule
def ReorderParameter(a: FunctionEntry, b: FunctionEntry, **kwargs):
    pa = [p.name for p in a.positionals]
    pb = [p.name for p in b.positionals]
    shared = set(pa) & set(pb)
    changed: "dict[str, tuple[int,int]]" = {}
    for item in shared:
        i = pa.index(item)
        j = pb.index(item)
        if i != j:
            changed[item] = i, j
    if changed:
        items = [f"{k}:{pa[i]}->{pb[j]}" for k, (i, j) in changed.items()]
        return RuleCheckResult(True, f"Reorder parameter: {', '.join(items)}.", {"data": changed})
    return False


@ParameterRules.rule
@changeParameter
def ChangeParameterOptional(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.optional != b.optional:
        return RuleCheckResult(True, f"Switch parameter {a.name} optional to {b.optional}.")
    return False


@ParameterRules.rule
@changeParameter
def ChangeParameterDefault(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.optional and b.optional and a.default != b.default:
        return RuleCheckResult(True, f"Change parameter {a.name} default from {a.default} to {b.default}.")
    return False


@ParameterRules.rule
@changeParameter
def RemoveVarPositional(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None and a.kind == ParameterKind.VarPositional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@ParameterRules.rule
@changeParameter
def RemoveVarKeyword(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None and a.kind == ParameterKind.VarKeyword:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()
