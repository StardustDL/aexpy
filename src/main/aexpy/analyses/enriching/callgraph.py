import ast
import logging
import textwrap
from ast import Call, NodeVisitor, expr, parse
from dataclasses import dataclass, field

from ..models import ApiCollection, FunctionEntry
from . import clearSrc


@dataclass
class Argument:
    name: str = ""
    value: expr | None = None
    iskwargs: bool = False
    raw: str = ""


@dataclass
class Callsite:
    target: str = ""
    arguments: list[Argument] = field(default_factory=list)
    value: Call | None = None
    raw: str = ""


@dataclass
class Caller:
    id: str = ""
    sites: list[Callsite] = field(default_factory=list)


@dataclass
class Callgraph:
    items: dict[str, Caller] = field(default_factory=dict)

    def add(self, item: Caller):
        self.items[item.id] = item


class CallsiteGetter(NodeVisitor):
    def __init__(self, result: Caller, src) -> None:
        super().__init__()
        self.result = result
        self.src = src

    def visit_Call(self, node: Call):
        site = Callsite(value=node)
        match node.func:
            case ast.Attribute() as attr:
                site.target = attr.attr
            case ast.Name() as name:
                site.target = name.id
        for arg in node.args:
            argu = Argument(
                value=arg, raw=ast.get_source_segment(self.src, arg))
            site.arguments.append(argu)
        for arg in node.keywords:
            argu = Argument(name=arg.arg, value=arg.value, iskwargs=arg.arg is None,
                            raw=ast.get_source_segment(self.src, arg.value))
            site.arguments.append(argu)
        self.result.sites.append(site)


def build(api: ApiCollection, logger: logging.Logger | None = None) -> Callgraph:
    logger = logger if logger is not None else logging.getLogger("callgraph")

    result = Callgraph()

    for func in api.funcs.values():
        caller = Caller(id=func.id)

        src = clearSrc(func.src)

        try:
            astree = parse(src)
        except Exception as ex:
            logger.error(
                f"Failed to parse code from {func.id}:\n{src}", exc_info=ex)
            result.add(caller)
            continue

        logger.debug(f"Visit AST of {func.id}")

        getter = CallsiteGetter(caller, src)
        getter.visit(astree)

        result.add(caller)

    return result
