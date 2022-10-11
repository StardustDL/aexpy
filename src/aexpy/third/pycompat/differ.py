import code
import pathlib
import subprocess
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import json
from aexpy.diffing import Differ
from aexpy.diffing.differs.checkers import DiffConstraint, diffcons, fortype
from aexpy.diffing.differs.default import ConstraintDiffer
from aexpy.diffing.evaluators.checkers import EvalRule
from aexpy.diffing.evaluators.default import RuleEvaluator
from aexpy.environments.conda import CondaEnvironment
from aexpy.extracting.environments import (EnvirontmentExtractor,
                                           ExecutionEnvironment)
from aexpy.models import (ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.description import FunctionEntry
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline
from aexpy.producers import ProducerOptions
from aexpy.reporting import Reporter as Base


@fortype(FunctionEntry)
@diffcons
def AddRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pb) - set(pa)

    items = []

    for item in new:
        para = b.getParameter(item)
        assert para
        if not para.optional:
            items.append(item)
    return [DiffEntry(message=f"Add required parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffcons
def RemoveRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) - set(pb)

    items = []

    for item in new:
        para = a.getParameter(item)
        assert para
        if not para.optional:
            items.append(item)

    return [DiffEntry(message=f"Remove required parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffcons
def AddOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pb) - set(pa)

    items = []

    for item in new:
        para = b.getParameter(item)
        assert para
        if not para.optional:
            items.append(item)

    return [DiffEntry(message=f"Add optional parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffcons
def RemoveOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) - set(pb)

    items = []

    for item in new:
        para = a.getParameter(item)
        assert para
        if not para.optional:
            items.append(item)

    return [DiffEntry(message=f"Remove optional parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffcons
def ReorderParameter(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        for titem in new:
            if item == titem:
                continue
            if pa.index(item) < pa.index(titem) and pb.index(item) > pb.index(titem):
                items.append((item, titem))

    return [DiffEntry(message=f"Reorder parameter ({a.id}): {item} & {titem}") for item, titem in items]


@fortype(FunctionEntry)
@diffcons
def AddParameterDefault(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        ppa, ppb = a.getParameter(item), b.getParameter(item)
        assert ppa and ppb
        if not ppa.optional and ppb.optional:
            items.append((item, ppb.default))

    return [DiffEntry(message=f"Add parameter default ({a.id}): {item} = {value}") for item, value in items]


@fortype(FunctionEntry)
@diffcons
def RemoveParameterDefault(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        ppa, ppb = a.getParameter(item), b.getParameter(item)
        assert ppa and ppb
        if ppa.optional and not ppb.optional:
            items.append((item, ppa.default))

    return [DiffEntry(message=f"Remove parameter default ({a.id}): {item} = {value}") for item, value in items]


@fortype(FunctionEntry)
@diffcons
def ChangeParameterDefault(a: "FunctionEntry", b: "FunctionEntry", dold: "ApiDescription", dnew: "ApiDescription"):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        ppa, ppb = a.getParameter(item), b.getParameter(item)
        assert ppa and ppb
        if ppa.optional and ppb.optional:
            da = ppa.default
            db = ppb.default
            if da != "___complex_type___" and db != "___complex_type___" and da != db:
                items.append((item, da, db))

    return [DiffEntry(message=f"Change parameter default ({a.id}): {item} = {da} -> {db}") for item, da, db in items]


class PDiffer(ConstraintDiffer):
    def __init__(self, logger: "Logger | None" = None, constraints: "list[DiffConstraint] | None" = None) -> None:
        constraints = constraints or []

        from aexpy.diffing.differs.contraints import (aliases, attributes, classes,
                                                      externals, functions, modules,
                                                      parameters, types)

        constraints.append(classes.AddClass)
        constraints.append(classes.RemoveClass)
        constraints.append(functions.AddFunction)
        constraints.append(functions.RemoveFunction)
        constraints.append(AddRequiredParameter)
        constraints.append(RemoveRequiredParameter)
        constraints.append(ReorderParameter)
        constraints.append(AddOptionalParameter)
        constraints.append(RemoveOptionalParameter)
        constraints.append(AddParameterDefault)
        constraints.append(RemoveParameterDefault)
        constraints.append(ChangeParameterDefault)
        constraints.append(attributes.AddAttribute)
        constraints.append(attributes.RemoveAttribute)

        super().__init__(logger, constraints)


class PEvaluator(RuleEvaluator):
    def __init__(self, logger: "Logger | None" = None, rules: "list[EvalRule] | None" = None) -> None:
        rules = rules or []

        from aexpy.diffing.evaluators import evals
        from aexpy.diffing.evaluators.checkers import rankAt

        rules.append(evals.AddClass)
        rules.append(evals.RemoveClass)
        rules.append(evals.AddFunction)
        rules.append(evals.RemoveFunction)
        rules.append(rankAt("AddRequiredParameter", BreakingRank.High))
        rules.append(rankAt("RemoveRequiredParameter", BreakingRank.High))
        rules.append(rankAt("ReorderParameter", BreakingRank.High))
        rules.append(rankAt("AddOptionalParameter", BreakingRank.High))
        rules.append(rankAt("RemoveOptionalParameter", BreakingRank.High))
        rules.append(rankAt("AddParameterDefault", BreakingRank.High))
        rules.append(rankAt("RemoveParameterDefault", BreakingRank.High))
        rules.append(rankAt("ChangeParameterDefault", BreakingRank.High))
        rules.append(evals.AddAttribute)
        rules.append(evals.RemoveAttribute)

        super().__init__(logger, rules)


class CombinedDiffer(Differ):
    def diff(self, old: "ApiDescription", new: "ApiDescription", product: "ApiDifference"):
        PDiffer(self.logger).diff(old, new, product)
        PEvaluator(self.logger).diff(old, new, product)
