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

from aexpy.analyses.enriching.mypyserver import PackageMypyServer

from ..models import (ApiCollection, ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry,
                      Parameter, ParameterKind)
from . import AnalysisInfo, Enricher, callgraph, clearSrc


logger = logging.getLogger("type")


def encodeType(type: Type | None) -> str:
    if type is None:
        return ""
    try:
        result = type.serialize()
        if isinstance(result, str):
            result = {
                "stringType": result
            }
        return base64.b64encode(json.dumps(result).encode("utf-8")).decode("utf-8")
    except Exception as ex:
        logger.error(f"Failed to encode type {type}.", exc_info=ex)
        return ""


def decodeType(typeStr: str) -> dict | str | None:
    if typeStr == "":
        return None
    try:
        dic = json.loads(base64.b64decode(
            typeStr.encode("utf-8")).decode("utf-8"))
        if "stringType" in dic:
            dic = dic["stringType"]  # str
        # return deserialize_type(dic)
        return dic
    except Exception as ex:
        logger.error(f"Failed to decode type {typeStr}.", exc_info=ex)
        return None


class TypeEnricher(Enricher):
    def __init__(self, server: PackageMypyServer, logger: logging.Logger | None = None) -> None:
        super().__init__()
        self.server = server
        self.logger = logger if logger is not None else logging.getLogger(
            "type-enrich")

    def enrich(self, api: ApiCollection) -> None:
        for entry in api.entries.values():
            match entry:
                case ModuleEntry() as module:
                    pass
                case ClassEntry() as cls:
                    pass
                case FunctionEntry() as func:
                    item = self.server.element(func)
                    if item:
                        type = item[0].type
                        if type is None:
                            func.type = ""
                        else:
                            func.type = str(type)
                        func.typeData = encodeType(type)
                        if isinstance(type, CallableType):
                            func.returnType = str(type.ret_type)
                            for para in func.parameters:
                                if para.name not in type.arg_names:
                                    continue
                                typara = type.argument_by_name(para.name)
                                para.type = str(typara.typ)
                                para.typeData = encodeType(typara.typ)
                case AttributeEntry() as attr:
                    item = self.server.element(attr)
                    if item:
                        attr.type = str(item[0].type)
                        attr.typeData = encodeType(item[0].type)
