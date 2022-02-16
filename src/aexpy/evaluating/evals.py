import dataclasses
from typing import Any
from uuid import uuid1
from aexpy.models import ApiDifference
from aexpy.models.description import FunctionEntry, ParameterKind
from aexpy.models.difference import BreakingRank, DiffEntry
from .checkers import RuleEvaluatorCollection, forkind, ruleeval, RuleEvaluator, rankAt


RuleEvals = RuleEvaluatorCollection()

AddModule = rankAt("AddModule", BreakingRank.Compatible)
RemoveModule = rankAt("RemoveModule", BreakingRank.High)
AddClass = rankAt("AddClass", BreakingRank.Compatible)
RemoveClass = rankAt("RemoveClass", BreakingRank.High)
ChangeBaseClass = rankAt("ChangeBaseClass", BreakingRank.Medium)
ChangeAbstractBaseClass = rankAt(
    "ChangeAbstractBaseClass", BreakingRank.Medium)
AddAlias = rankAt("AddAlias", BreakingRank.Compatible)
RemoveAlias = rankAt("RemoveAlias", BreakingRank.High)
ChangeAlias = rankAt("ChangeAlias", BreakingRank.Medium)
AddFunction = rankAt("AddFunction", BreakingRank.Compatible)
RemoveFunction = rankAt("RemoveFunction", BreakingRank.High)
AddAttribute = rankAt("AddAttribute", BreakingRank.Compatible)
RemoveAttribute = rankAt("RemoveAttribute", BreakingRank.High)

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
RuleEvals.ruleeval(ChangeBaseClass)
RuleEvals.ruleeval(ChangeAbstractBaseClass)
RuleEvals.ruleeval(AddAlias)
RuleEvals.ruleeval(RemoveAlias)
RuleEvals.ruleeval(ChangeAlias)
RuleEvals.ruleeval(AddFunction)
RuleEvals.ruleeval(RemoveFunction)
RuleEvals.ruleeval(AddAttribute)
RuleEvals.ruleeval(RemoveAttribute)
RuleEvals.ruleeval(ChangeParameterDefault)
RuleEvals.ruleeval(ReorderParameter)
RuleEvals.ruleeval(AddVarKeywordCandidate)
RuleEvals.ruleeval(RemoveVarKeywordCandidate)


@RuleEvals.ruleeval
@ruleeval
def ChangeParameterOptional(entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
    data: "list[tuple[str, str, dict[str, Any]]]" = entry.data["data"]
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    res: list[DiffEntry] = []

    for pa, pb, pdata in data:
        if fb.getParameter(pb).optional:
            res.append(DiffEntry("", "AddParameterDefault", BreakingRank.Compatible,
                       f"Change parameter to optional ({fa.id}): {pa}, {pb}.", {"old": pa, "new": pb, "data": pdata}, fa, fb))
        else:
            res.append(DiffEntry("", "RemoveParameterDefault", BreakingRank.High,
                       f"Change parameter to required ({fa.id}): {pa}, {pb}.", {"old": pa, "new": pb, "data": pdata}, fa, fb))

    return res


@RuleEvals.ruleeval
@ruleeval
def AddParameter(entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
    data: "list[tuple[str, str, dict[str, Any]]]" = entry.data["data"]
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    res: list[DiffEntry] = []

    for pa, pb, pdata in data:
        para = fb.getParameter(pb)
        if para.kind == ParameterKind.VarPositional:
            res.append(DiffEntry("", "AddVarPositional", BreakingRank.Compatible,
                       f"Add var positional parameter ({fa.id}): {pb}.", {"name": pb, "data": pdata}, fa, fb))
        elif para.kind == ParameterKind.VarKeyword:
            res.append(DiffEntry("", "AddVarKeyword", BreakingRank.Compatible,
                       f"Add var positional parameter ({fa.id}): {pb}.", {"name": pb, "data": pdata}, fa, fb))
        elif para.optional:
            res.append(DiffEntry("", "AddOptionalParameter", BreakingRank.Low,
                       f"Add optional parameter ({fa.id}): {pb}.", {"name": pb, "data": pdata}, fa, fb))
        else:
            res.append(DiffEntry("", "AddRequiredParameter", BreakingRank.High,
                       f"Add required parameter ({fa.id}): {pb}.", {"name": pb, "data": pdata}, fa, fb))

    return res


@RuleEvals.ruleeval
@ruleeval
def RemoveParameter(entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
    data: "list[tuple[str, str, dict[str, Any]]]" = entry.data["data"]
    fa: FunctionEntry = entry.old
    fb: FunctionEntry = entry.new

    res: list[DiffEntry] = []

    for pa, pb, pdata in data:
        para = fa.getParameter(pa)
        if para.kind == ParameterKind.VarPositional:
            res.append(DiffEntry("", "RemoveVarPositional", BreakingRank.High,
                       f"Remove var positional parameter ({fa.id}): {pa}.", {"name": pa, "data": pdata}, fa, fb))
        elif para.kind == ParameterKind.VarKeyword:
            res.append(DiffEntry("", "RemoveVarKeyword", BreakingRank.High,
                       f"Remove var positional parameter ({fa.id}): {pa}.", {"name": pa, "data": pdata}, fa, fb))
        elif para.optional:
            res.append(DiffEntry("", "RemoveOptionalParameter", BreakingRank.High,
                       f"Remove optional parameter ({fa.id}): {pa}.", {"name": pa, "data": pdata}, fa, fb))
        else:
            res.append(DiffEntry("", "RemoveRequiredParameter", BreakingRank.High,
                       f"Remove required parameter ({fa.id}): {pa}.", {"name": pa, "data": pdata}, fa, fb))

    return res
