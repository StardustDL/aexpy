import itertools
from itertools import zip_longest
from typing import Callable, OrderedDict
import functools

from aexpy.analyses.models import (ApiEntry, ClassEntry, CollectionEntry,
                                   FieldEntry, FunctionEntry, ModuleEntry,
                                   Parameter, ParameterKind)

from .models import DiffRule, RuleCheckResult


def add(a: ApiEntry | None, b: ApiEntry | None):
    if a is None and b is not None:
        return RuleCheckResult(True, f"{b.id}")
    return RuleCheckResult.unsatisfied()


def remove(a: ApiEntry | None, b: ApiEntry | None):
    if a is not None and b is None:
        return RuleCheckResult(True, f"{a.id}")
    return RuleCheckResult.unsatisfied()


def addMember(a: CollectionEntry | None, b: CollectionEntry | None):
    sub = b.members.keys() - a.members.keys()
    if len(sub) > 0:
        return RuleCheckResult(True, f"{list(sub)}")
    return RuleCheckResult.unsatisfied()


def removeMember(a: CollectionEntry | None, b: CollectionEntry | None):
    sub = a.members.keys() - b.members.keys()
    if len(sub) > 0:
        return RuleCheckResult(True, f"{list(sub)}")
    return RuleCheckResult.unsatisfied()


def changeMember(a: CollectionEntry | None, b: CollectionEntry | None):
    inter = a.members.keys() & b.members.keys()
    changed = {}
    for k in inter:
        if a.members[k] != b.members[k]:
            changed[k] = f"{a.members[k]} -> {b.members[k]}"
    if len(changed) > 0:
        return RuleCheckResult(True, f"{changed}")
    return RuleCheckResult.unsatisfied()


def changeBases(a: ClassEntry, b: ClassEntry):
    changed = set(a.bases) ^ set(b.bases)
    if len(changed) > 0:
        return RuleCheckResult(True, f"{changed}")
    return RuleCheckResult.unsatisfied()


def changeFieldType(a: FieldEntry, b: FieldEntry):
    if a.type != b.type:
        return RuleCheckResult(True, f"{a.type} -> {b.type}")
    return RuleCheckResult.unsatisfied()


def changeReturnType(a: FunctionEntry, b: FunctionEntry):
    if a.returnType != b.returnType:
        return RuleCheckResult(True, f"{a.returnType} -> {b.returnType}")
    return RuleCheckResult.unsatisfied()


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


def changeParameter(checker: Callable[[Parameter | None, Parameter | None], RuleCheckResult]):
    @functools.wraps(checker)
    def wrapper(a: FunctionEntry | None, b: FunctionEntry | None):
        results = []
        for x, y in matchParameters(a, b):
            result = checker(x, y)
            if result:
                results.append(
                    f"{x.name if x else 'None'} & {y.name if y else 'None'}{': ' + result.message if result.message else ''}")
        return RuleCheckResult(len(results) > 0, str(results))

    return wrapper


@changeParameter
def addRP(a: Parameter | None, b: Parameter | None):
    if a is None and b is not None and not b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def removeRP(a: Parameter | None, b: Parameter | None):
    if a is not None and b is None and not a.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def addOP(a: Parameter | None, b: Parameter | None):
    if a is None and b is not None and b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def removeOP(a: Parameter | None, b: Parameter | None):
    if a is not None and b is None and a.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def reorderP(a: Parameter | None, b: Parameter | None):
    if a is not None and b is not None and \
            a.isPositional() and b.isPositional() and \
            a.name != b.name:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def addPD(a: Parameter | None, b: Parameter | None):
    if a is not None and b is not None and not a.optional and b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def removePD(a: Parameter | None, b: Parameter | None):
    if a is not None and b is not None and a.optional and not b.optional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def changePD(a: Parameter | None, b: Parameter | None):
    if a is not None and b is not None and a.optional and b.optional and a.default != b.default:
        return RuleCheckResult(True, f"{a.default} -> {b.default}")
    return RuleCheckResult.unsatisfied()


@changeParameter
def changePT(a: Parameter | None, b: Parameter | None):
    if a is not None and b is not None and a.type != b.type:
        return RuleCheckResult(True, f"{a.type} -> {b.type}")
    return RuleCheckResult.unsatisfied()


@changeParameter
def removeVP(a: Parameter | None, b: Parameter | None):
    if a is not None and b is None and a.kind == ParameterKind.VarPositional:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


@changeParameter
def removeVKP(a: Parameter | None, b: Parameter | None):
    if a is not None and b is None and a.kind == ParameterKind.VarKeyword:
        return RuleCheckResult.satisfied()
    return RuleCheckResult.unsatisfied()


addrules = [
    DiffRule("AddModule", add).fortype(ModuleEntry, True),
    DiffRule("AddClass", add).fortype(ClassEntry, True),
    DiffRule("AddFunction", add).fortype(FunctionEntry, True),
    DiffRule("AddField", add).fortype(FieldEntry, True),
]

removerules = [
    DiffRule("RemoveModule", remove).fortype(ModuleEntry, True),
    DiffRule("RemoveClass", remove).fortype(ClassEntry, True),
    DiffRule("RemoveFunction", remove).fortype(FunctionEntry, True),
    DiffRule("RemoveField", remove).fortype(FieldEntry, True),
]

memberrules = [
    DiffRule("AddMember", addMember).fortype(CollectionEntry),
    DiffRule("RemoveMember", removeMember).fortype(CollectionEntry),
    DiffRule("ChangeMember", changeMember).fortype(CollectionEntry)
]

pararules = [
    DiffRule("AddRequiredParameter", addRP).fortype(FunctionEntry),
    DiffRule("RemoveRequiredParameter", removeRP).fortype(FunctionEntry),
    DiffRule("AddOptionalParameter", addOP).fortype(FunctionEntry),
    DiffRule("RemoveOptionalParameter", removeOP).fortype(FunctionEntry),
    DiffRule("ReorderParameter", reorderP).fortype(FunctionEntry),
    DiffRule("AddParameterDefault", addPD).fortype(FunctionEntry),
    DiffRule("RemoveParameterDefault", removePD).fortype(FunctionEntry),
    DiffRule("ChangeParameterDefault", changePD).fortype(FunctionEntry),
    DiffRule("ChangeParameterType", changePT).fortype(FunctionEntry),
    DiffRule("RemoveVarPositional", removeVP).fortype(FunctionEntry),
    DiffRule("RemoveVarKeyword", removeVKP).fortype(FunctionEntry),
]

otherrules = [
    DiffRule("ChangeBaseClass", changeBases).fortype(ClassEntry),
    DiffRule("ChangeFieldType", changeFieldType).fortype(FieldEntry),
    DiffRule("ChangeReturnType", changeReturnType).fortype(FunctionEntry),
]
