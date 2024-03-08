import ast
import logging
from ast import Call, NodeVisitor, parse
from typing import override

from ....models import ApiDescription, ClassEntry, FunctionEntry
from ....models.description import ItemScope
from .. import clearSrc
from . import Argument, Caller, Callgraph, CallgraphBuilder, Callsite


class CallsiteGetter(NodeVisitor):
    def __init__(self, /, result: Caller, src: str) -> None:
        super().__init__()
        self.result = result
        self.src = src

    def visit_Call(self, /, node: Call):
        site = Callsite(value=node)
        site.targetValue = node.func
        match node.func:
            case ast.Attribute() as attr:
                site.targets = [attr.attr]
            case ast.Name() as name:
                site.targets = [name.id]
        for arg in node.args:
            argu = Argument(value=arg, raw=ast.get_source_segment(self.src, arg) or "")
            site.arguments.append(argu)
        for arg in node.keywords:
            argu = Argument(
                name=arg.arg or "<none>",
                value=arg.value,
                iskwargs=arg.arg is None,
                raw=ast.get_source_segment(self.src, arg.value) or "",
            )
            site.arguments.append(argu)
        self.result.sites.append(site)

        super().generic_visit(node)


class FunctionResolver:
    def __init__(self, /, api: ApiDescription) -> None:
        self.api = api
        self.subclasses = {}

    def dispatch(self, /, cls: ClassEntry, name: str):
        if name in cls.members:
            return cls.members[name]
        for item in cls.mros:
            tcls = self.api[item]
            if not isinstance(tcls, ClassEntry):
                continue
            if name in tcls.members:
                return tcls.members[name]
        return None

    def matchArguments(self, /, func: FunctionEntry, arguments: list[Argument]):
        for index, arg in enumerate(arguments):
            if arg.name:
                if func.getParameter(arg.name) is None:
                    return False
            else:
                tn = index + (0 if func.scope == ItemScope.Static else 1)
                if tn >= len(func.parameters) or not func.parameters[tn].isPositional:
                    return False
        return True

    def resolveMethods(self, /, cls: ClassEntry, name: str):
        result: list[str] = []
        if cls.id not in self.subclasses:
            sc = []
            for item in self.api.classes.values():
                if cls.id in item.bases:
                    sc.append(item)
            self.subclasses[cls.id] = sc
        sc = self.subclasses[cls.id]
        for item in sc:
            target = self.dispatch(item, name)
            if target:
                result.append(target)
        return list(set(result))

    def resolveTargetsByName(self, /, name: str, arguments: list[Argument]):

        resolvedTargets: list[str] = []

        for targetEntry in self.api.name(name):
            if isinstance(targetEntry, ClassEntry):
                if f"{targetEntry.id}.__init__" in self.api:
                    targetEntry = self.api[f"{targetEntry.id}.__init__"]
                else:
                    resolvedTargets.append(
                        f"{targetEntry.id}.__init__"
                    )  # get constructor
            if isinstance(targetEntry, FunctionEntry):
                if self.matchArguments(targetEntry, arguments):
                    resolvedTargets.append(targetEntry.id)

        return resolvedTargets

    def resolveTargetByName(self, /, name: str, arguments: list[Argument]):
        result = self.resolveTargetsByName(name, arguments)
        if len(result) == 1:
            return [result[0]]
        return []


class BasicCallgraphBuilder(CallgraphBuilder):
    def __init__(self, /, logger: logging.Logger | None = None) -> None:
        super().__init__()
        self.logger = (
            logger.getChild("callgraph-basic")
            if logger is not None
            else logging.getLogger("callgraph-basic")
        )

    @override
    def build(self, /, api):
        result = Callgraph()
        resolver = FunctionResolver(api)

        for func in api.functions.values():
            caller = Caller(id=func.id)

            src = clearSrc(func.src)

            try:
                astree = parse(src)
            except Exception:
                self.logger.error(
                    f"Failed to parse code from {func.id}:\n{src}", exc_info=True
                )
                result.add(caller)
                continue

            self.logger.debug(f"Visit AST of {func.id}")

            getter = CallsiteGetter(caller, src)
            getter.visit(astree)

            for site in caller.sites:
                if len(site.targets) == 0:
                    continue

                site.targets = resolver.resolveTargetsByName(
                    site.targets[0], site.arguments
                )

            result.add(caller)

        return result
