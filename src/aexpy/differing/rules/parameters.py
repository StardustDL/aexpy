import functools
import itertools
from itertools import zip_longest
from typing import Callable, Iterator, OrderedDict

from aexpy.models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                      CollectionEntry, FunctionEntry, ModuleEntry,
                                      Parameter, ParameterKind, SpecialEntry, SpecialKind)
from aexpy.models.difference import DiffEntry

from ..checkers import (DiffRule, DiffRuleCollection,
                        diffrule, fortype)


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


def changeParameter(checker: "Callable[[Parameter | None, Parameter | None, FunctionEntry, FunctionEntry], list[DiffEntry]]"):
    @fortype(FunctionEntry)
    @diffrule
    @functools.wraps(checker)
    def wrapper(a: FunctionEntry, b: FunctionEntry, **kwargs):
        results: "list[tuple[Parameter | None, Parameter | None, list[DiffEntry]]]" = [
        ]
        for x, y in matchParameters(a, b):
            result = checker(x, y, a, b)
            if result:
                results.append((x, y, result))

        ret: "list[DiffEntry]" = []

        for x, y, result in results:
            for item in result:
                item.data["old"] = x.name if x else ""
                item.data["new"] = y.name if y else ""
                ret.append(item)

        return ret

    return wrapper


@ParameterRules.rule
@changeParameter
def AddParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is None and b is not None:
        return [DiffEntry(message=f"Add parameter ({old.id}): {b.name}.")]
    return []


@ParameterRules.rule
@changeParameter
def RemoveParameter(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is None:
        return [DiffEntry(message=f"Remove parameter ({new.id}): {a.name}.")]
    return []


@ParameterRules.rule
@changeParameter
def ChangeParameterOptional(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.optional != b.optional:
        return [DiffEntry(message=f"Switch parameter ({old.id}) {a.name}({b.name}) optional to {b.optional}.", data={"optional": b.optional})]
    return []


@ParameterRules.rule
@changeParameter
def ChangeParameterDefault(a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry):
    if a is not None and b is not None and a.optional and b.optional and a.default != b.default:
        return [DiffEntry(message=f"Change parameter ({old.id}) {a.name}({b.name}) default from {a.default} to {b.default}.", data={"olddefault": a.default, "newdefault": b.default})]
    return []


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
        return [DiffEntry(message=f"Reorder parameter ({a.id}): {'; '.join(items)}.", data={"data": changed})]
    return []


@ParameterRules.rule
@fortype(FunctionEntry)
@diffrule
def AddVarKeywordCandidate(a: FunctionEntry, b: FunctionEntry, **kwargs):
    pa = [p.name for p in a.candidates]
    pb = [p.name for p in b.candidates]
    changed = set(pb) - set(pa)
    if changed:
        return [DiffEntry(message=f"Add var keyword candidate ({b.id}): {'; '.join(changed)}.", data={"data": changed})]
    return []


@ParameterRules.rule
@fortype(FunctionEntry)
@diffrule
def RemoveVarKeywordCandidate(a: FunctionEntry, b: FunctionEntry, **kwargs):
    pa = [p.name for p in a.candidates]
    pb = [p.name for p in b.candidates]
    changed = set(pa) - set(pb)
    if changed:
        return [DiffEntry(message=f"Remove var keyword candidate ({a.id}): {'; '.join(changed)}.", data={"data": changed})]
    return []
