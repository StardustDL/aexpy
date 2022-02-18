import code
from logging import Logger
import pathlib
from aexpy import getCacheDirectory
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.producer import ProducerOptions
from aexpy.reporting import Reporter as Base
from logging import Logger
from pathlib import Path
import subprocess
from uuid import uuid1
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.preprocessing import getDefault
from aexpy.extracting.environments import EnvirontmentExtractor, ExtractorEnvironment
from aexpy.extracting.environments.conda import CondaEnvironment
from aexpy.differing.default import RuleDiffer
from aexpy.evaluating.default import Evaluator as BaseEvaluator
from aexpy.models import ApiBreaking, ApiDifference, Release, ApiDescription
from aexpy.pipelines import Pipeline

from datetime import datetime, timedelta
import json
from typing import Callable
import subprocess

from aexpy.differing.checkers import DiffRule, RuleCheckResult, diffrule, fortype
from aexpy.models.description import FunctionEntry
from aexpy.models.difference import BreakingRank


@fortype(FunctionEntry)
@diffrule
def AddRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pb) - set(pa)

    items = []

    for item in new:
        if not b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Add required parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def RemoveRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) - set(pb)

    items = []

    for item in new:
        if not a.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Remove required parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def AddOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pb) - set(pa)

    items = []

    for item in new:
        if b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Add optional parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def RemoveOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) - set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Remove optional parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def ReorderParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        for titem in new:
            if item == titem:
                continue
            if pa.index(item) < pa.index(titem) and pb.index(item) > pb.index(titem):
                items.append((item, titem))

    if items:
        return RuleCheckResult(True, f"Reorder parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def AddParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if not a.getParameter(item).optional and b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Add parameter default: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def RemoveParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional and not b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Remove parameter default: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def ChangeParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional and b.getParameter(item).optional:
            da = a.getParameter(item).default
            db = b.getParameter(item).default
            if da != "___complex_type___" and db != "___complex_type___" and da != db:
                items.append((item, da, db))

    if items:
        return RuleCheckResult(True, f"Change parameter default: {'; '.join(items)}")

    return False


class Differ(RuleDiffer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[DiffRule] | None" = None) -> None:
        rules = rules or []

        from aexpy.differing.rules import (modules, classes, functions,
                                           attributes, parameters, types, aliases, externals)

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
