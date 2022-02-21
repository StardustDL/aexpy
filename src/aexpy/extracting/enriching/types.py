import ast
import logging
from ast import NodeVisitor
from dataclasses import Field, asdict, dataclass, field
import json
import base64

import mypy
from mypy import find_sources
from mypy.version import __version__
from mypy.dmypy_server import Server
from mypy.options import Options
from mypy.nodes import (
    ARG_POS, ARG_STAR, ARG_NAMED, ARG_STAR2, ARG_NAMED_OPT, FuncDef, MypyFile, SymbolTable,
    SymbolNode, TypeInfo, Node, Expression, ReturnStmt, NameExpr, SymbolTableNode, Var,
    AssignmentStmt, Context, RefExpr, FuncBase, MemberExpr, CallExpr
)
from mypy.types import (
    Type, AnyType, TypeOfAny, CallableType, UnionType, NoneTyp, Instance, is_optional, deserialize_type, CallableType
)
from mypy.traverser import TraverserVisitor
from mypy.infer import infer_function_type_arguments

from ..third.mypyserver import PackageMypyServer

from aexpy.models import ApiDescription

from aexpy.models.description import (ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry, TypeInfo as MTypeInfo,
                                      Parameter, ParameterKind)
from . import Enricher, clearSrc


def encodeType(type: Type | None, logger: "logging.Logger") -> MTypeInfo | None:
    if type is None:
        return None
    try:
        result = type.serialize()
        if isinstance(result, str):
            return MTypeInfo(str(type), {
                "stringType": result
            })
        else:
            return MTypeInfo(str(type), json.loads(json.dumps(result)))
    except Exception as ex:
        logger.error(f"Failed to encode type {type}.", exc_info=ex)
        return None


class TypeEnricher(Enricher):
    def __init__(self, server: "PackageMypyServer", logger: "logging.Logger | None" = None) -> None:
        super().__init__()
        self.server = server
        self.logger = logger.getChild("type-enrich") if logger is not None else logging.getLogger(
            "type-enrich")

    def enrich(self, api: "ApiDescription") -> None:
        for entry in api.entries.values():
            try:
                match entry:
                    case ModuleEntry() as module:
                        pass
                    case ClassEntry() as cls:
                        pass
                    case FunctionEntry() as func:
                        item = self.server.element(func)
                        if item:
                            type = item[0].type
                            func.type = encodeType(type, self.logger)
                            if isinstance(type, CallableType):
                                func.returnType = encodeType(
                                    type.ret_type, self.logger)
                                for para in func.parameters:
                                    if para.name not in type.arg_names:
                                        continue
                                    typara = type.argument_by_name(para.name)
                                    para.type = encodeType(
                                        typara.typ, self.logger)
                    case AttributeEntry() as attr:
                        item = self.server.element(attr)
                        if item:
                            attr.type = encodeType(item[0].type, self.logger)
            except Exception as ex:
                self.logger.error(
                    f"Failed to enrich entry {entry.id}.", exc_info=ex)
