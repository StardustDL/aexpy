import ast
import logging
from ast import NodeVisitor
from dataclasses import asdict

from ..models import (ApiCollection, ApiEntry, ClassEntry, FunctionEntry,
                      Parameter, ParameterKind)
from . import AnalysisInfo, Enricher, callgraph, clearSrc


def _try_addkwc_parameter(entry: FunctionEntry, parameter: Parameter, logger: logging.Logger):
    """Return if add successfully"""
    if len([x for x in entry.parameters if x.name == parameter.name]) != 0:  # has same name parameter
        return False
    data = asdict(parameter)
    data.pop("kind")
    entry.parameters.append(
        Parameter(kind=ParameterKind.VarKeywordCandidate, **data))
    logger.debug(f"Detect candidate {entry.id}: {parameter.name}")
    return True


class KwargChangeGetter(NodeVisitor):
    def __init__(self, result: FunctionEntry, logger: logging.Logger) -> None:
        super().__init__()
        self.logger = logger
        self.result = result
        self.kwarg = result.getVarKeywordParameter().name

    def add(self, name: str):
        _try_addkwc_parameter(self.result, Parameter(
            name=name, optional=True), self.logger)

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
            self.logger.error(
                f"Failed to detect in call {ast.unparse(node)}", exc_info=ex)

    def visit_Subscript(self, node: ast.Subscript):
        try:
            match node:
                # kwargs["abc"]
                case ast.Subscript(value=ast.Name() as name, slice=ast.Constant(value=str())) if name.id == self.kwarg:
                    self.add(node.slice.value)
        except Exception as ex:
            self.logger.error(
                f"Failed to detect in subscript {ast.unparse(node)}", exc_info=ex)


class KwargsEnricher(Enricher):
    def __init__(self, cg: callgraph.Callgraph, logger: logging.Logger | None = None) -> None:
        super().__init__()
        self.logger = logger if logger is not None else logging.getLogger(
            "kwargs-enrich")
        self.cg = cg

    def enrich(self, api: ApiCollection):
        self.enrichByDictChange(api)
        self.enrichByCallgraph(api)

    def enrichByDictChange(self, api: ApiCollection):
        for func in api.funcs.values():
            if func.getVarKeywordParameter():
                src = clearSrc(func.src)
                try:
                    astree = ast.parse(src)
                except Exception as ex:
                    self.logger.error(
                        f"Failed to parse code from {func.id}:\n{src}", exc_info=ex)
                    continue
                KwargChangeGetter(func, self.logger).visit(astree)

    def enrichByCallgraph(self, api: ApiCollection):
        cg = self.cg

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
                    for target in site.targets:
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

                        targetEntry = api.entries.get(target)

                        if not isinstance(targetEntry, FunctionEntry):
                            continue

                        # ignore magic methods
                        if targetEntry.name.startswith("__") and targetEntry.name != "__init__":
                            continue

                        self.logger.debug(
                            f"Enrich by call edge: {callerEntry.id} -> {targetEntry.id}")

                        for arg in targetEntry.parameters:
                            if arg.isKeyword():
                                changed = changed or _try_addkwc_parameter(
                                    callerEntry, arg, self.logger)
