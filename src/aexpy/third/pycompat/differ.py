import code
import pathlib
import subprocess
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import getCacheDirectory, json
from aexpy.differing.checkers import DiffRule, diffrule, fortype
from aexpy.differing.default import RuleDiffer
from aexpy.environments.conda import CondaEnvironment
from aexpy.evaluating.default import Evaluator as BaseEvaluator
from aexpy.extracting.environments import (EnvirontmentExtractor,
                                           ExecutionEnvironment)
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.description import FunctionEntry
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline
from aexpy.preprocessing import getDefault
from aexpy.producer import ProducerOptions
from aexpy.reporting import Reporter as Base


@fortype(FunctionEntry)
@diffrule
def AddRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pb) - set(pa)

    items = []

    for item in new:
        if not b.getParameter(item).optional:
            items.append(item)
    return [DiffEntry(message=f"Add required parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffrule
def RemoveRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) - set(pb)

    items = []

    for item in new:
        if not a.getParameter(item).optional:
            items.append(item)

    return [DiffEntry(message=f"Remove required parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffrule
def AddOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pb) - set(pa)

    items = []

    for item in new:
        if b.getParameter(item).optional:
            items.append(item)

    return [DiffEntry(message=f"Add optional parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffrule
def RemoveOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) - set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional:
            items.append(item)

    return [DiffEntry(message=f"Remove optional parameter ({a.id}): {item}") for item in items]


@fortype(FunctionEntry)
@diffrule
def ReorderParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
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
@diffrule
def AddParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if not a.getParameter(item).optional and b.getParameter(item).optional:
            items.append((item, b.getParameter(item).default))

    return [DiffEntry(message=f"Add parameter default ({a.id}): {item} = {value}") for item, value in items]


@fortype(FunctionEntry)
@diffrule
def RemoveParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional and not b.getParameter(item).optional:
            items.append((item, a.getParameter(item).default))

    return [DiffEntry(message=f"Remove parameter default ({a.id}): {item} = {value}") for item, value in items]


@fortype(FunctionEntry)
@diffrule
def ChangeParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = [p.name for p in a.parameters]
    pb = [p.name for p in b.parameters]

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional and b.getParameter(item).optional:
            da = a.getParameter(item).default
            db = b.getParameter(item).default
            if da != "___complex_type___" and db != "___complex_type___" and da != db:
                items.append((item, da, db))

    return [DiffEntry(message=f"Change parameter default ({a.id}): {item} = {da} -> {db}") for item, da, db in items]


class Differ(RuleDiffer):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "pycompat"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[DiffRule] | None" = None) -> None:
        rules = rules or []

        from aexpy.differing.rules import (aliases, attributes, classes,
                                           externals, functions, modules,
                                           parameters, types)

        rules.append(classes.AddClass)
        rules.append(classes.RemoveClass)
        rules.append(functions.AddFunction)
        rules.append(functions.RemoveFunction)
        rules.append(AddRequiredParameter)
        rules.append(RemoveRequiredParameter)
        rules.append(ReorderParameter)
        rules.append(AddOptionalParameter)
        rules.append(RemoveOptionalParameter)
        rules.append(AddParameterDefault)
        rules.append(RemoveParameterDefault)
        rules.append(ChangeParameterDefault)
        rules.append(attributes.AddAttribute)
        rules.append(attributes.RemoveAttribute)

        super().__init__(logger, cache, options, rules)
