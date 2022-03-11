import dataclasses
from typing import Any
from uuid import uuid1

from aexpy.evaluating.typing import ApiTypeCompatibilityChecker
from aexpy.extracting.main.basic import isprivateName
from aexpy.models import ApiDescription, ApiDifference
from aexpy.models.description import (EXTERNAL_ENTRYID, ApiEntry,
                                      AttributeEntry, ClassEntry,
                                      FunctionEntry, ModuleEntry,
                                      ParameterKind, SpecialEntry, SpecialKind)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.models.typing import UnknownType

from .checkers import EvalRule, EvalRuleCollection, forkind, rankAt, ruleeval

RuleEvals = EvalRuleCollection()

AddModule = rankAt("AddModule", BreakingRank.Compatible)
AddClass = rankAt("AddClass", BreakingRank.Compatible)
AddBaseClass = rankAt("AddBaseClass", BreakingRank.Medium)
RemoveBaseClass = rankAt("RemoveBaseClass", BreakingRank.High)
ImplementAbstractBaseClass = rankAt(
    "ImplementAbstractBaseClass", BreakingRank.Compatible)
DeimplementAbstractBaseClass = rankAt(
    "DeimplementAbstractBaseClass", BreakingRank.High)
ChangeMethodResolutionOrder = rankAt(
    "ChangeMethodResolutionOrder", BreakingRank.Low)
AddFunction = rankAt("AddFunction", BreakingRank.Compatible)

ChangeParameterDefault = rankAt(
    "ChangeParameterDefault", BreakingRank.Low)
ReorderParameter = rankAt("ReorderParameter", BreakingRank.High)

AddVarKeywordCandidate = rankAt(
    "AddVarKeywordCandidate", BreakingRank.Compatible)
RemoveVarKeywordCandidate = rankAt(
    "RemoveVarKeywordCandidate", BreakingRank.Medium)

RuleEvals.ruleeval(AddModule)
RuleEvals.ruleeval(AddClass)
RuleEvals.ruleeval(AddBaseClass)
RuleEvals.ruleeval(RemoveBaseClass)
RuleEvals.ruleeval(ImplementAbstractBaseClass)
RuleEvals.ruleeval(DeimplementAbstractBaseClass)
RuleEvals.ruleeval(ChangeMethodResolutionOrder)
RuleEvals.ruleeval(AddFunction)
RuleEvals.ruleeval(ChangeParameterDefault)
RuleEvals.ruleeval(ReorderParameter)
RuleEvals.ruleeval(AddVarKeywordCandidate)
RuleEvals.ruleeval(RemoveVarKeywordCandidate)

AddAttribute = rankAt("AddAttribute", BreakingRank.Compatible)
RemoveAttribute = rankAt("RemoveAttribute", BreakingRank.High)


@RuleEvals.ruleeval
@ruleeval
def RemoveModule(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    mod: "ModuleEntry" = entry.old
    if mod.private:
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def RemoveClass(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    mod: "ClassEntry" = entry.old
    if mod.private:
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def RemoveFunction(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    mod: "FunctionEntry" = entry.old
    if mod.private:
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def AddAttribute(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    attr: "AttributeEntry" = entry.new

    entry.rank = BreakingRank.Compatible

    if attr.bound:
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

    if attr.bound:
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
        entry.message = f"Add external alias ({entry.old.id}): {name} -> {entry.data['target']}"


@RuleEvals.ruleeval
@ruleeval
def RemoveAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    entry.rank = BreakingRank.High
    name = entry.data["name"]
    target = old.entries.get(entry.data["target"])
    if isprivateName(name):
        entry.rank = BreakingRank.Low

    if target is None or (isinstance(target, SpecialEntry) and target.kind == SpecialKind.External):
        entry.rank = BreakingRank.Low
        entry.kind = "RemoveExternalAlias"
        entry.message = f"Remove external alias ({entry.old.id}): {name} -> {entry.data['target']}"


@RuleEvals.ruleeval
@ruleeval
def ChangeAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    entry.rank = BreakingRank.Medium
    name = entry.data["name"]
    oldtarget = old.entries.get(entry.data["old"])
    newtarget = new.entries.get(entry.data["new"])

    if isprivateName(name):
        entry.rank = BreakingRank.Low
    
    if oldtarget is None or (isinstance(oldtarget, SpecialEntry) and oldtarget.kind == SpecialKind.External):
        if newtarget is None or (isinstance(newtarget, SpecialEntry) and newtarget.kind == SpecialKind.External):
            entry.rank = BreakingRank.Low
            entry.kind = "ChangeExternalAlias"
            entry.message = f"Change external alias ({entry.old.id}): {name}: {entry.data['old']} -> {entry.data['new']}"


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterOptional(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new
    data = entry.data

    if data["newoptional"]:
        entry.kind = "AddParameterDefault"
        entry.rank = BreakingRank.Compatible
        entry.message = f"Change parameter to optional ({fa.id}): {data['old']}({data['new']})."
    else:
        entry.kind = "RemoveParameterDefault"
        entry.rank = BreakingRank.High
        entry.message = f"Change parameter to required ({fa.id}): {data['old']}({data['new']})."


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
        entry.message = f"Add var positional parameter ({fa.id}): {data['new']}."
    elif para.kind == ParameterKind.VarKeyword:
        entry.kind = "AddVarKeyword"
        entry.rank = BreakingRank.Compatible
        entry.message = f"Add var keyword parameter ({fa.id}): {data['new']}."
    elif para.optional:
        entry.kind = "AddOptionalParameter"
        entry.rank = BreakingRank.Low
        entry.message = f"Add optional parameter ({fa.id}): {data['new']}."
    else:
        entry.kind = "AddRequiredParameter"
        entry.rank = BreakingRank.High
        entry.message = f"Add required parameter ({fa.id}): {data['new']}."


@RuleEvals.ruleeval
@ruleeval
def RemoveParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    data = entry.data
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    para = fa.getParameter(data["old"])

    if para.kind == ParameterKind.VarPositional:
        entry.kind = "RemoveVarPositional"
        entry.rank = BreakingRank.High
        entry.message = f"Remove var positional parameter ({fa.id}): {data['old']}."
    elif para.kind == ParameterKind.VarKeyword:
        entry.kind = "RemoveVarKeyword"
        entry.rank = BreakingRank.High
        entry.message = f"Remove var keyword parameter ({fa.id}): {data['old']}."
    elif para.optional:
        entry.kind = "RemoveOptionalParameter"
        entry.rank = BreakingRank.High
        entry.message = f"Remove optional parameter ({fa.id}): {data['old']}."
    else:
        entry.kind = "RemoveRequiredParameter"
        entry.rank = BreakingRank.High
        entry.message = f"Remove required parameter ({fa.id}): {data['old']}."


@RuleEvals.ruleeval
@ruleeval
def ChangeAttributeType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: AttributeEntry = entry.old
    enew: AttributeEntry = entry.new

    if eold.type.type is not None and enew.type.type is not None:
        result = ApiTypeCompatibilityChecker(
            new).isCompatibleTo(eold.type.type, enew.type.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium


@RuleEvals.ruleeval
@ruleeval
def ChangeReturnType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: FunctionEntry = entry.old
    enew: FunctionEntry = entry.new

    if eold.returnType.type is not None and enew.returnType.type is not None:
        result = ApiTypeCompatibilityChecker(new).isCompatibleTo(
            eold.returnType.type, enew.returnType.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: FunctionEntry = entry.old
    enew: FunctionEntry = entry.new

    pold = eold.getParameter(entry.data["old"])
    pnew = enew.getParameter(entry.data["new"])

    if pold.type.type is not None and pnew.type.type is not None:
        result = ApiTypeCompatibilityChecker(
            new).isCompatibleTo(pold.type.type, pnew.type.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium
