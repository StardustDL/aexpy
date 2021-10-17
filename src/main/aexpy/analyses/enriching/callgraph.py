from ast import Call, NodeVisitor, expr, parse
import ast
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging
from ..models import FunctionEntry, ApiCollection


@dataclass
class Argument:
    name: str = ""
    value: Optional[expr] = None
    iskwargs: bool = False
    raw: str = ""


@dataclass
class Callsite:
    target: str = ""
    arguments: List[Argument] = field(default_factory=list)
    value: Optional[Call] = None
    raw: str = ""


@dataclass
class Caller:
    id: str = ""
    sites: List[Callsite] = field(default_factory=list)


@dataclass
class Callgraph:
    items: Dict[str, Caller] = field(default_factory=dict)

    def add(self, item: Caller):
        self.items[item.id] = item


class CallsiteGetter(NodeVisitor):
    def __init__(self, result: Caller, src) -> None:
        super().__init__()
        self.result = result
        self.src = src

    def visit_Call(self, node: Call):
        site = Callsite(value=node)
        if isinstance(node.func, ast.Attribute):
            site.target = node.func.attr
        elif isinstance(node.func, ast.Name):
            site.target = node.func.id
        for arg in node.args:
            argu = Argument(
                value=arg, raw=ast.get_source_segment(self.src, arg))
            site.arguments.append(argu)
        for arg in node.keywords:
            argu = Argument(name=arg.arg, value=arg.value, iskwargs=arg.arg is None,
                            raw=ast.get_source_segment(self.src, arg.value))
            site.arguments.append(argu)
        self.result.sites.append(site)


def build(api: ApiCollection) -> Callgraph:
    logger = logging.getLogger("callgraph")

    result = Callgraph()

    for func in api.funcs.values():
        logger.info(func.id)

        caller = Caller(id=func.id)

        try:
            astree = parse(func.src)
        except Exception as ex:
            logger.error(ex)
            logger.error(func.src)
            result.add(caller)
            continue

        getter = CallsiteGetter(caller, func.src)
        getter.visit(astree)

        result.add(caller)

    return result
