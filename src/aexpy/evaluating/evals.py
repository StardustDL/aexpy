import dataclasses
from typing import Any
from uuid import uuid1
from aexpy.analyses.models import ParameterKind
from aexpy.models import ApiDifference
from aexpy.models.description import FunctionEntry
from aexpy.models.difference import BreakingRank, DiffEntry
from .checkers import RuleEvaluatorCollection, forkind, ruleeval, RuleEvaluator


def rankAt(rank: "BreakingRank"):
    def checker(entry: "DiffEntry", diff: "ApiDifference") -> "list[DiffEntry]":
        return [dataclasses.replace(entry, rank=rank)]

    return checker


RuleEvals = RuleEvaluatorCollection()

AddModule = RuleEvaluator("AddModule", rankAt(BreakingRank.Compatible))
RemoveModule = RuleEvaluator("RemoveModule", rankAt(BreakingRank.High))
AddClass = RuleEvaluator("AddClass", rankAt(BreakingRank.Compatible))
RemoveClass = RuleEvaluator("RemoveClass", rankAt(BreakingRank.High))
ChangeBaseClass = RuleEvaluator("ChangeBaseClass", rankAt(BreakingRank.Medium))
ChangeAbstractBaseClass = RuleEvaluator(
    "ChangeAbstractBaseClass", rankAt(BreakingRank.Medium))
AddAlias = RuleEvaluator("AddAlias", rankAt(BreakingRank.Compatible))
RemoveAlias = RuleEvaluator("RemoveAlias", rankAt(BreakingRank.High))
ChangeAlias = RuleEvaluator("ChangeAlias", rankAt(BreakingRank.Medium))
AddFunction = RuleEvaluator("AddFunction", rankAt(BreakingRank.Compatible))
RemoveFunction = RuleEvaluator("RemoveFunction", rankAt(BreakingRank.High))
AddAttribute = RuleEvaluator("AddAttribute", rankAt(BreakingRank.Compatible))
RemoveAttribute = RuleEvaluator("RemoveAttribute", rankAt(BreakingRank.High))

ChangeParameterDefault = RuleEvaluator(
    "ChangeParameterDefault", rankAt(BreakingRank.Low))
ReorderParameter = RuleEvaluator("ReorderParameter", rankAt(BreakingRank.High))

AddVarKeywordCandidate = RuleEvaluator(
    "AddVarKeywordCandidate", rankAt(BreakingRank.Compatible))
RemoveVarKeywordCandidate = RuleEvaluator(
    "RemoveVarKeywordCandidate", rankAt(BreakingRank.Medium))

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
                       f"Change parameter to optional: ({pa}, {pb}) of {fa.id}.", {"old": pa, "new": pb, "data": pdata}, fa, fb))
        else:
            res.append(DiffEntry("", "RemoveParameterDefault", BreakingRank.High,
                       f"Change parameter to required: ({pa}, {pb}) of {fa.id}.", {"old": pa, "new": pb, "data": pdata}, fa, fb))

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
                       f"Add var positional parameter: {pb} of {fa.id}.", {"name": pb, "data": pdata}, fa, fb))
        elif para.kind == ParameterKind.VarKeyword:
            res.append(DiffEntry("", "AddVarKeyword", BreakingRank.Compatible,
                       f"Add var positional parameter: {pb} of {fa.id}.", {"name": pb, "data": pdata}, fa, fb))
        elif para.optional:
            res.append(DiffEntry("", "AddOptionalParameter", BreakingRank.Low,
                       f"Add optional parameter: {pb} of {fa.id}.", {"name": pb, "data": pdata}, fa, fb))
        else:
            res.append(DiffEntry("", "AddRequiredParameter", BreakingRank.High,
                       f"Add required parameter: {pb} of {fa.id}.", {"name": pb, "data": pdata}, fa, fb))

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
                       f"Remove var positional parameter: {pa} of {fa.id}.", {"name": pa, "data": pdata}, fa, fb))
        elif para.kind == ParameterKind.VarKeyword:
            res.append(DiffEntry("", "RemoveVarKeyword", BreakingRank.High,
                       f"Remove var positional parameter: {pa} of {fa.id}.", {"name": pa, "data": pdata}, fa, fb))
        elif para.optional:
            res.append(DiffEntry("", "RemoveOptionalParameter", BreakingRank.High,
                       f"Remove optional parameter: {pa} of {fa.id}.", {"name": pa, "data": pdata}, fa, fb))
        else:
            res.append(DiffEntry("", "RemoveRequiredParameter", BreakingRank.High,
                       f"Remove required parameter: {pa} of {fa.id}.", {"name": pa, "data": pdata}, fa, fb))

    return res
