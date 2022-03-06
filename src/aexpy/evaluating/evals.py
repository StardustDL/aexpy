import dataclasses
from typing import Any
from uuid import uuid1

from aexpy.models import ApiDifference
from aexpy.models.description import (EXTERNAL_ENTRYID, ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry,
                                      ParameterKind, SpecialEntry, SpecialKind)
from aexpy.models.difference import BreakingRank, DiffEntry

from .checkers import (RuleEvaluator, RuleEvaluatorCollection, forkind, rankAt,
                       ruleeval)

RuleEvals = RuleEvaluatorCollection()

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
ChangeAlias = rankAt("ChangeAlias", BreakingRank.Medium)
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
RuleEvals.ruleeval(ChangeAlias)
RuleEvals.ruleeval(AddFunction)
RuleEvals.ruleeval(ChangeParameterDefault)
RuleEvals.ruleeval(ReorderParameter)
RuleEvals.ruleeval(AddVarKeywordCandidate)
RuleEvals.ruleeval(RemoveVarKeywordCandidate)

AddAttribute = rankAt("AddAttribute", BreakingRank.Compatible)
RemoveAttribute = rankAt("RemoveAttribute", BreakingRank.High)


def isprivate(entry: ApiEntry) -> bool:
    names = [entry.id, *entry.alias]
    for alias in names:
        pri = False
        for item in alias.split("."):
            if item.startswith("_") and not (item.startswith("__") and item.endswith("__")):
                pri = True
                break
        if not pri:
            return False
    return True


@RuleEvals.ruleeval
@ruleeval
def RemoveModule(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    mod: "ModuleEntry" = entry.old
    if isprivate(mod):
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def RemoveClass(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    mod: "ClassEntry" = entry.old
    if isprivate(mod):
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def RemoveFunction(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    mod: "FunctionEntry" = entry.old
    if isprivate(mod):
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High


@RuleEvals.ruleeval
@ruleeval
def AddAttribute(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    attr: "AttributeEntry" = entry.new

    entry.rank = BreakingRank.Compatible

    if attr.bound:
        entry.kind = "AddInstanceAttribute"
        entry.message = f"Add instance attribute ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


@RuleEvals.ruleeval
@ruleeval
def RemoveAttribute(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    attr: "AttributeEntry" = entry.old

    if isprivate(attr):
        entry.rank = BreakingRank.Low
    else:
        entry.rank = BreakingRank.High

    if attr.bound:
        entry.kind = "RemoveInstanceAttribute"
        entry.message = f"Remove instance attribute ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


@RuleEvals.ruleeval
@ruleeval
def AddAlias(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    entry.rank = BreakingRank.Compatible
    name = entry.data["name"]
    target = entry.data["target"]
    if target == EXTERNAL_ENTRYID:
        entry.kind = "AddExternalAlias"
        entry.message = f"Add external alias ({entry.old.id}): {name} -> {target}"


@RuleEvals.ruleeval
@ruleeval
def RemoveAlias(entry: "DiffEntry", diff: "ApiDifference") -> "None":
    entry.rank = BreakingRank.High
    name = entry.data["name"]
    target = entry.data["target"]
    if target == EXTERNAL_ENTRYID:
        entry.rank = BreakingRank.Low
        entry.kind = "RemoveExternalAlias"
        entry.message = f"Remove external alias ({entry.old.id}): {name} -> {target}"


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterOptional(entry: "DiffEntry", diff: "ApiDifference") -> "None":
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
def AddParameter(entry: "DiffEntry", diff: "ApiDifference") -> None:
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
def RemoveParameter(entry: "DiffEntry", diff: "ApiDifference") -> None:
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
