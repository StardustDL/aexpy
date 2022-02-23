import dataclasses
from typing import Any
from uuid import uuid1

from aexpy.models import ApiDifference
from aexpy.models.description import (AttributeEntry, FunctionEntry,
                                      ParameterKind)
from aexpy.models.difference import BreakingRank, DiffEntry

from .checkers import (RuleEvaluator, RuleEvaluatorCollection, forkind, rankAt,
                       ruleeval)

RuleEvals = RuleEvaluatorCollection()

AddModule = rankAt("AddModule", BreakingRank.Compatible)
RemoveModule = rankAt("RemoveModule", BreakingRank.High)
AddClass = rankAt("AddClass", BreakingRank.Compatible)
RemoveClass = rankAt("RemoveClass", BreakingRank.High)
AddBaseClass = rankAt("AddBaseClass", BreakingRank.Medium)
RemoveBaseClass = rankAt("RemoveBaseClass", BreakingRank.High)
ImplementAbstractBaseClass = rankAt(
    "ImplementAbstractBaseClass", BreakingRank.Compatible)
DeimplementAbstractBaseClass = rankAt(
    "DeimplementAbstractBaseClass", BreakingRank.High)
ChangeMethodResolutionOrder = rankAt("ChangeMethodResolutionOrder", BreakingRank.Low)
AddAlias = rankAt("AddAlias", BreakingRank.Compatible)
RemoveAlias = rankAt("RemoveAlias", BreakingRank.High)
ChangeAlias = rankAt("ChangeAlias", BreakingRank.Medium)
AddFunction = rankAt("AddFunction", BreakingRank.Compatible)
RemoveFunction = rankAt("RemoveFunction", BreakingRank.High)

ChangeParameterDefault = rankAt(
    "ChangeParameterDefault", BreakingRank.Low)
ReorderParameter = rankAt("ReorderParameter", BreakingRank.High)

AddVarKeywordCandidate = rankAt(
    "AddVarKeywordCandidate", BreakingRank.Compatible)
RemoveVarKeywordCandidate = rankAt(
    "RemoveVarKeywordCandidate", BreakingRank.Medium)

RuleEvals.ruleeval(AddModule)
RuleEvals.ruleeval(RemoveModule)
RuleEvals.ruleeval(AddClass)
RuleEvals.ruleeval(RemoveClass)
RuleEvals.ruleeval(AddBaseClass)
RuleEvals.ruleeval(RemoveBaseClass)
RuleEvals.ruleeval(ImplementAbstractBaseClass)
RuleEvals.ruleeval(DeimplementAbstractBaseClass)
RuleEvals.ruleeval(AddAlias)
RuleEvals.ruleeval(RemoveAlias)
RuleEvals.ruleeval(ChangeAlias)
RuleEvals.ruleeval(AddFunction)
RuleEvals.ruleeval(RemoveFunction)
RuleEvals.ruleeval(ChangeParameterDefault)
RuleEvals.ruleeval(ReorderParameter)
RuleEvals.ruleeval(AddVarKeywordCandidate)
RuleEvals.ruleeval(RemoveVarKeywordCandidate)

AddAttribute = rankAt("AddAttribute", BreakingRank.Compatible)
RemoveAttribute = rankAt("RemoveAttribute", BreakingRank.High)


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

    entry.rank = BreakingRank.High

    if attr.bound:
        entry.kind = "RemoveInstanceAttribute"
        entry.message = f"Remove instance attribute ({attr.id.rsplit('.', 1)[0]}): {attr.name}"


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
