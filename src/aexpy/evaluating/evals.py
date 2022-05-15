import dataclasses
from typing import Any
from uuid import uuid1

from aexpy.evaluating.typing import ApiTypeCompatibilityChecker
from aexpy.extracting.main.base import isprivateName
from aexpy.models import ApiDescription, ApiDifference
from aexpy.models.description import (EXTERNAL_ENTRYID, ApiEntry,
                                      AttributeEntry, ClassEntry,
                                      FunctionEntry, ItemScope, ModuleEntry,
                                      ParameterKind, SpecialEntry, SpecialKind)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.models.typing import AnyType, TypeFactory, UnknownType, NoneType, CallableType, copyType

from .checkers import EvalRule, EvalRuleCollection, forkind, rankAt, ruleeval

RuleEvals = EvalRuleCollection()

AddModule = rankAt("AddModule", BreakingRank.Compatible)
RemoveModule = rankAt("RemoveModule", BreakingRank.High, BreakingRank.Low)
AddClass = rankAt("AddClass", BreakingRank.Compatible)
RemoveClass = rankAt("RemoveClass", BreakingRank.High, BreakingRank.Low)
AddBaseClass = rankAt("AddBaseClass", BreakingRank.Compatible)
RemoveBaseClass = rankAt(
    "RemoveBaseClass", BreakingRank.High, BreakingRank.Low)
ImplementAbstractBaseClass = rankAt(
    "ImplementAbstractBaseClass", BreakingRank.Compatible)
DeimplementAbstractBaseClass = rankAt(
    "DeimplementAbstractBaseClass", BreakingRank.High, BreakingRank.Low)
ChangeMethodResolutionOrder = rankAt(
    "ChangeMethodResolutionOrder", BreakingRank.Medium, BreakingRank.Low)
MoveParameter = rankAt(
    "MoveParameter", BreakingRank.High, BreakingRank.Low)

RuleEvals.ruleeval(AddModule)
RuleEvals.ruleeval(RemoveModule)
RuleEvals.ruleeval(AddClass)
RuleEvals.ruleeval(RemoveClass)
RuleEvals.ruleeval(AddBaseClass)
RuleEvals.ruleeval(ImplementAbstractBaseClass)
RuleEvals.ruleeval(DeimplementAbstractBaseClass)
RuleEvals.ruleeval(ChangeMethodResolutionOrder)
RuleEvals.ruleeval(MoveParameter)


@RuleEvals.ruleeval
@ruleeval
def RemoveBaseClass(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    eold = entry.old
    enew = entry.new
    name = entry.data["name"]
    if eold.private or enew.private or isprivateName(name):
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def AddFunction(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    attr: "FunctionEntry" = entry.new

    entry.rank = BreakingRank.Compatible

    if attr.scope != ItemScope.Static:
        entry.kind = "AddMethod"
        entry.message = f"Add method ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


@RuleEvals.ruleeval
@ruleeval
def RemoveFunction(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    attr: "FunctionEntry" = entry.old

    if attr.private:
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High

    if attr.scope != ItemScope.Static:
        entry.kind = "RemoveMethod"
        entry.message = f"Remove method ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


@RuleEvals.ruleeval
@ruleeval
def AddAttribute(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    attr: "AttributeEntry" = entry.new

    entry.rank = BreakingRank.Compatible

    if attr.scope == ItemScope.Instance:
        entry.kind = "AddInstanceAttribute"
        entry.message = f"Add instance attribute ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


@RuleEvals.ruleeval
@ruleeval
def RemoveAttribute(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    attr: "AttributeEntry" = entry.old

    if attr.private:
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High

    if attr.scope == ItemScope.Instance:
        entry.kind = "RemoveInstanceAttribute"
        entry.message = f"Remove instance attribute ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


@RuleEvals.ruleeval
@ruleeval
def AddAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    entry.rank = BreakingRank.Compatible
    name = entry.data["name"]
    target = new.entries.get(entry.data["target"])
    if target is None or (isinstance(target, SpecialEntry) and target.kind == SpecialKind.External):
        entry.kind = "AddExternalAlias"


@RuleEvals.ruleeval
@ruleeval
def RemoveAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    entry.rank = BreakingRank.High
    name = entry.data["name"]
    target = old.entries.get(entry.data["target"])
    if isprivateName(name) or entry.old.private:
        entry.rank = BreakingRank.Low

    if target is None or (isinstance(target, SpecialEntry) and target.kind == SpecialKind.External):
        entry.rank = BreakingRank.Low
        entry.kind = "RemoveExternalAlias"


@RuleEvals.ruleeval
@ruleeval
def ChangeAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    entry.rank = BreakingRank.Unknown
    name = entry.data["name"]
    oldtarget = old.entries.get(entry.data["old"])
    newtarget = new.entries.get(entry.data["new"])

    if isprivateName(name):
        entry.rank = BreakingRank.Unknown

    if oldtarget is None or (isinstance(oldtarget, SpecialEntry) and oldtarget.kind == SpecialKind.External):
        if newtarget is None or (isinstance(newtarget, SpecialEntry) and newtarget.kind == SpecialKind.External):
            entry.rank = BreakingRank.Unknown
            entry.kind = "ChangeExternalAlias"


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterDefault(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new
    data = entry.data

    parent = old.entries.get(fa.parent)
    if isinstance(parent, ClassEntry):
        entry.rank = BreakingRank.Medium
    else:
        entry.rank = BreakingRank.Compatible
    
    if fa.private:
        entry.rank = min(entry.rank, BreakingRank.Low)


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterOptional(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new
    data = entry.data

    if data["newoptional"]:
        entry.kind = "AddParameterDefault"
        parent = old.entries.get(fa.parent)
        if isinstance(parent, ClassEntry):
            entry.rank = BreakingRank.Medium
        else:
            entry.rank = BreakingRank.Compatible
    else:
        entry.kind = "RemoveParameterDefault"
        entry.rank = BreakingRank.High

    if fa.private:
        entry.rank = min(entry.rank, BreakingRank.Low)


@RuleEvals.ruleeval
@ruleeval
def AddParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    data = entry.data
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    para = fb.getParameter(data["new"])

    if para.kind == ParameterKind.VarPositional:
        entry.kind = "AddVarPositional"
        entry.rank = BreakingRank.Compatible
    elif para.kind == ParameterKind.VarKeyword:
        entry.kind = "AddVarKeyword"
        entry.rank = BreakingRank.Compatible
    elif para.kind == ParameterKind.VarKeywordCandidate:
        if para.optional:
            entry.kind = "AddOptionalCandidate"
            entry.rank = BreakingRank.Compatible
        else:
            entry.kind = "AddRequiredCandidate"
            entry.rank = BreakingRank.Medium
    elif para.optional:
        entry.kind = "AddOptionalParameter"
        parent = old.entries.get(fa.parent)
        if isinstance(parent, ClassEntry):
            entry.rank = BreakingRank.Medium
        else:
            entry.rank = BreakingRank.Compatible
    else:
        entry.kind = "AddRequiredParameter"
        entry.rank = BreakingRank.High

    if fa.private:
        entry.rank = min(entry.rank, BreakingRank.Low)


@RuleEvals.ruleeval
@ruleeval
def RemoveParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    data = entry.data
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    para = fa.getParameter(data["old"])

    entry.rank = BreakingRank.High

    if para.kind == ParameterKind.VarPositional:
        entry.kind = "RemoveVarPositional"
    elif para.kind == ParameterKind.VarKeyword:
        entry.kind = "RemoveVarKeyword"
    elif para.kind == ParameterKind.VarKeywordCandidate:
        if para.source == fa.id and not fb.transmitKwargs:
            # local use and no transmit kwargs
            entry.rank = BreakingRank.Compatible
        else:
            entry.rank = BreakingRank.Medium
        if para.optional:
            entry.kind = "RemoveOptionalCandidate"
        else:
            entry.kind = "RemoveRequiredCandidate"
    elif para.optional:
        entry.kind = "RemoveOptionalParameter"
    else:
        entry.kind = "RemoveRequiredParameter"

    if fa.private:
        entry.rank = min(entry.rank, BreakingRank.Low)


@RuleEvals.ruleeval
@ruleeval
def ChangeAttributeType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: AttributeEntry = entry.old
    enew: AttributeEntry = entry.new

    if eold.type.type is not None and enew.type.type is not None:
        result = ApiTypeCompatibilityChecker(
            new).isCompatibleTo(enew.type.type, eold.type.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium

    if eold.private:
        entry.rank = min(entry.rank, BreakingRank.Low)


@RuleEvals.ruleeval
@ruleeval
def ChangeReturnType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: FunctionEntry = entry.old
    enew: FunctionEntry = entry.new

    if eold.returnType.type is not None and enew.returnType.type is not None:
        told = eold.returnType.type

        if isinstance(told, NoneType):
            told = TypeFactory.any()

        result = ApiTypeCompatibilityChecker(new).isCompatibleTo(
            enew.returnType.type, told)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium

    if eold.private:
        entry.rank = min(entry.rank, BreakingRank.Low)


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: FunctionEntry = entry.old
    enew: FunctionEntry = entry.new

    pold = eold.getParameter(entry.data["old"])
    pnew = enew.getParameter(entry.data["new"])

    if pold.type.type is not None and pnew.type.type is not None:
        tnew = copyType(pnew.type.type)

        if isinstance(tnew, CallableType):
            if isinstance(tnew.ret, NoneType):
                # a parameter: any -> none, is same as any -> any (ignore return means return any thing is ok)
                tnew.ret = TypeFactory.any()

        result = ApiTypeCompatibilityChecker(
            new).isCompatibleTo(pold.type.type, tnew)

        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium

    if eold.private:
        entry.rank = min(entry.rank, BreakingRank.Low)
