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
from aexpy.models.typing import AnyType, UnknownType

from .checkers import EvalRule, EvalRuleCollection, forkind, rankAt, ruleeval

RuleEvals = EvalRuleCollection()

AddModule = rankAt("AddModule", BreakingRank.Compatible)
RemoveModule = rankAt("RemoveModule", BreakingRank.High, BreakingRank.Low)
AddClass = rankAt("AddClass", BreakingRank.Compatible)
RemoveClass = rankAt("RemoveClass", BreakingRank.High, BreakingRank.Low)
AddBaseClass = rankAt("AddBaseClass", BreakingRank.Low)
RemoveBaseClass = rankAt(
    "RemoveBaseClass", BreakingRank.High, BreakingRank.Low)
ImplementAbstractBaseClass = rankAt(
    "ImplementAbstractBaseClass", BreakingRank.Compatible)
DeimplementAbstractBaseClass = rankAt(
    "DeimplementAbstractBaseClass", BreakingRank.High, BreakingRank.Low)
ChangeMethodResolutionOrder = rankAt(
    "ChangeMethodResolutionOrder", BreakingRank.Low)
AddFunction = rankAt("AddFunction", BreakingRank.Compatible)
RemoveFunction = rankAt("RemoveFunction", BreakingRank.High, BreakingRank.Low)
ChangeParameterDefault = rankAt(
    "ChangeParameterDefault", BreakingRank.Low)
ReorderParameter = rankAt(
    "ReorderParameter", BreakingRank.High, BreakingRank.Low)

RuleEvals.ruleeval(AddModule)
RuleEvals.ruleeval(RemoveModule)
RuleEvals.ruleeval(AddClass)
RuleEvals.ruleeval(RemoveClass)
RuleEvals.ruleeval(AddBaseClass)
RuleEvals.ruleeval(RemoveBaseClass)
RuleEvals.ruleeval(ImplementAbstractBaseClass)
RuleEvals.ruleeval(DeimplementAbstractBaseClass)
RuleEvals.ruleeval(ChangeMethodResolutionOrder)
RuleEvals.ruleeval(AddFunction)
RuleEvals.ruleeval(RemoveFunction)
RuleEvals.ruleeval(ChangeParameterDefault)
RuleEvals.ruleeval(ReorderParameter)


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


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterOptional(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "None":
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new
    data = entry.data

    if data["newoptional"]:
        entry.kind = "AddParameterDefault"
        parent = old.entries.get(fa.id.rsplit(".", 1)[0])
        if isinstance(parent, ClassEntry):
            entry.rank = BreakingRank.Low
        else:
            entry.rank = BreakingRank.Compatible
    else:
        entry.kind = "RemoveParameterDefault"
        entry.rank = BreakingRank.High if not fa.private else BreakingRank.Low


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
            entry.rank = BreakingRank.Medium if not fa.private else BreakingRank.Low
    elif para.optional:
        entry.kind = "AddOptionalParameter"
        parent = old.entries.get(fa.id.rsplit(".", 1)[0])
        if isinstance(parent, ClassEntry):
            entry.rank = BreakingRank.Low
        else:
            entry.rank = BreakingRank.Compatible
    else:
        entry.kind = "AddRequiredParameter"
        entry.rank = BreakingRank.High if not fa.private else BreakingRank.Low


@RuleEvals.ruleeval
@ruleeval
def RemoveParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    data = entry.data
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    para = fa.getParameter(data["old"])

    entry.rank = BreakingRank.High if not fa.private else BreakingRank.Low

    if para.kind == ParameterKind.VarPositional:
        entry.kind = "RemoveVarPositional"
    elif para.kind == ParameterKind.VarKeyword:
        entry.kind = "RemoveVarKeyword"
    elif para.kind == ParameterKind.VarKeywordCandidate:
        if para.source == fa.id:
            entry.rank = BreakingRank.Compatible
        else:
            entry.rank = BreakingRank.Medium if not fa.private else BreakingRank.Low
        if para.optional:
            entry.kind = "RemoveOptionalCandidate"
        else:
            entry.kind = "RemoveRequiredCandidate"
    elif para.optional:
        entry.kind = "RemoveOptionalParameter"
    else:
        entry.kind = "RemoveRequiredParameter"


@RuleEvals.ruleeval
@ruleeval
def ChangeAttributeType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: AttributeEntry = entry.old
    enew: AttributeEntry = entry.new

    if eold.type.type is not None and enew.type.type is not None:
        if isinstance(eold.type.type, AnyType) and eold.annotation == "":
            return
        if isinstance(enew.type.type, AnyType) and enew.annotation == "":
            return

        result = ApiTypeCompatibilityChecker(
            new).isCompatibleTo(enew.type.type, eold.type.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium if not eold.private else BreakingRank.Low


@RuleEvals.ruleeval
@ruleeval
def ChangeReturnType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: FunctionEntry = entry.old
    enew: FunctionEntry = entry.new

    if eold.returnType.type is not None and enew.returnType.type is not None:
        if isinstance(eold.returnType.type, AnyType) and not eold.returnAnnotation == "":
            return
        if isinstance(enew.returnType.type, AnyType) and not enew.returnAnnotation == "":
            return

        result = ApiTypeCompatibilityChecker(new).isCompatibleTo(
            enew.returnType.type, eold.returnType.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium if not eold.private else BreakingRank.Low


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
    eold: FunctionEntry = entry.old
    enew: FunctionEntry = entry.new

    pold = eold.getParameter(entry.data["old"])
    pnew = enew.getParameter(entry.data["new"])

    if pold.type.type is not None and pnew.type.type is not None:
        if isinstance(pold.type.type, AnyType) and pold.annotation == "":
            return
        if isinstance(pnew.type.type, AnyType) and pnew.annotation == "":
            return

        result = ApiTypeCompatibilityChecker(
            new).isCompatibleTo(pold.type.type, pnew.type.type)
        if result == True:
            entry.rank = BreakingRank.Compatible
        elif result == False:
            entry.rank = BreakingRank.Medium if not eold.private else BreakingRank.Low
