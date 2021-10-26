import ast
import logging
from ast import NodeVisitor
from dataclasses import asdict

from ..models import (ApiCollection, ApiEntry, ClassEntry, FunctionEntry,
                      Parameter, ParameterKind)
from . import Enricher, callgraph

logger = logging.getLogger("kwargs-enrich")


def _try_addkwc_parameter(entry: FunctionEntry, parameter: Parameter):
    """Return if add successfully"""
    if len([x for x in entry.parameters if x.name == parameter.name]) != 0:  # has same name parameter
        return False
    data = asdict(parameter)
    data.pop("kind")
    entry.parameters.append(
        Parameter(kind=ParameterKind.VarKeywordCandidate, **data))
    logger.info(f"{entry.id}: {parameter.name}")
    return True


class KwargChangeGetter(NodeVisitor):
    def __init__(self, result: FunctionEntry) -> None:
        super().__init__()
        self.result = result
        self.kwarg = result.getVarKeywordParameter().name

    def add(self, name: str):
        _try_addkwc_parameter(self.result, Parameter(name=name, optional=True))

    def visit_Call(self, node: ast.Call):
        try:
            method = None

            match node.func:
                # kwargs.<method> call
                case ast.Attribute(value=ast.Name() as name) as attr if name.id == self.kwarg:
                    method = attr.attr

            if method in {"get", "pop", "setdefault"}:
                arg = node.args[0]
                match arg:
                    # kwargs.get("abc")
                    case ast.Constant(value=str()):
                        self.add(arg.value)
        except Exception as ex:
            logger.error(ex)

    def visit_Subscript(self, node: ast.Subscript):
        try:
            match node:
                # kwargs["abc"]
                case ast.Subscript(value=ast.Name() as name, slice=ast.Constant(value=str())) if name.id == self.kwarg:
                    self.add(node.slice.value)
        except Exception as ex:
            logger.error(ex)


class KwargsEnricher(Enricher):
    def enrich(self, api: ApiCollection):
        self.enrichByDictChange(api)
        self.enrichByCallgraph(api)

    def enrichByDictChange(self, api: ApiCollection):
        for func in api.funcs.values():
            if func.getVarKeywordParameter():
                try:
                    astree = ast.parse(func.src)
                except Exception as ex:
                    logger.error(ex)
                    logger.error(func.src)
                    continue
                KwargChangeGetter(func).visit(astree)

    def enrichByCallgraph(self, api: ApiCollection):
        cg = callgraph.build(api)

        changed = True

        while changed:
            changed = False

            for caller in cg.items.values():
                callerEntry: FunctionEntry = api.entries[caller.id]

                kwarg = callerEntry.getVarKeywordParameter()

                if kwarg is None:
                    continue

                kwargName = kwarg.name

                for site in caller.sites:
                    if site.target.startswith("__"):  # ignore magic methods
                        continue

                    hasKwargsRef = False
                    for arg in site.arguments:
                        if arg.iskwargs:
                            match arg.value:
                                # has **kwargs argument
                                case ast.Name() as name if name.id == kwargName:
                                    hasKwargsRef = True
                                    break

                    if not hasKwargsRef:
                        continue

                    targetEntries = api.names.get(site.target)

                    if targetEntries is None:
                        continue

                    for targetEntry in targetEntries:
                        if isinstance(targetEntry, ClassEntry):
                            targetEntry = api.entries.get(
                                f"{targetEntry.id}.__init__")  # get constructor

                        if not isinstance(targetEntry, FunctionEntry):
                            continue

                        logger.info(f"{callerEntry.id} -> {targetEntry.id}")

                        for arg in targetEntry.parameters:
                            if arg.isKeyword():
                                changed = changed or _try_addkwc_parameter(
                                    callerEntry, arg)
