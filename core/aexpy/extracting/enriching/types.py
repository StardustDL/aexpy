import ast
import base64
import logging
from ast import NodeVisitor
from dataclasses import Field, asdict, dataclass, field
from typing import Iterable, Optional, override

import mypy
from mypy import find_sources
from mypy.dmypy_server import Server
from mypy.infer import infer_function_type_arguments
from mypy.build import State
from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_POS,
    ARG_STAR,
    ARG_STAR2,
    AssignmentStmt,
    CallExpr,
    Context,
    Expression,
    FuncBase,
    FuncDef,
    MemberExpr,
    MypyFile,
    NameExpr,
    Node,
    RefExpr,
    ReturnStmt,
    SymbolNode,
    SymbolTable,
    SymbolTableNode,
    TypeInfo,
    Var,
)
from mypy.options import Options
from mypy.traverser import TraverserVisitor
from mypy.types import (
    AnyType,
    CallableArgument,
    CallableType,
    DeletedType,
    EllipsisType,
    ErasedType,
    Instance,
    LiteralType,
    NoneTyp,
    NoneType,
    Overloaded,
    ParamSpecType,
    PartialType,
    PlaceholderType,
    RawExpressionType,
    SyntheticTypeVisitor,
    TupleType,
    Type,
    TypeAliasType,
    TypedDictType,
    TypeList,
    TypeOfAny,
    TypeStrVisitor,
    TypeType,
    TypeVarType,
    UnboundType,
    UninhabitedType,
    UnionType,
    deserialize_type,
    get_proper_type,
    TypeVisitor
)
from mypy.util import IdMapper
from mypy.version import __version__

import json
from aexpy.models import ApiDescription
from aexpy.models import typing as mtyping
from aexpy.models.description import (
    ApiEntry,
    AttributeEntry,
    ClassEntry,
    FunctionEntry,
    ModuleEntry,
    Parameter,
    ParameterKind,
)
from aexpy.models.description import TypeInfo as MTypeInfo
from aexpy.models.typing import TypeType as MType, LiteralType as MLiteralType
from aexpy.models.typing import TypeFactory

from ..third.mypyserver import PackageMypyServer
from . import Enricher, clearSrc

class Translator(TypeVisitor[MType]):
    def visit_unbound_type(self, t):
        return TypeFactory.unknown(str(t))

    def visit_any(self, t):
        return TypeFactory.any()

    def visit_none_type(self, t):
        return TypeFactory.none()

    def visit_uninhabited_type(self, t):
        return TypeFactory.none()

    def visit_erased_type(self, t):
        return TypeFactory.unknown(str(t))

    def visit_deleted_type(self, t):
        return TypeFactory.unknown(str(t))

    def visit_instance(self, t):
        last_known_value: mtyping.LiteralType | None = None
        if t.last_known_value is not None:
            raw_last_known_value = t.last_known_value.accept(self)
            assert isinstance(raw_last_known_value, mtyping.LiteralType)  # type: ignore[misc]
            last_known_value = raw_last_known_value
        name = t.type.fullname or t.type.name
        if not name:
            return TypeFactory.unknown(str(t))
        baseType = mtyping.ClassType(id=str(name))
        if t.args:
            return TypeFactory.generic(baseType, *self.translate_types(t.args))
        else:
            return baseType

    def visit_type_var(self, t):
        return TypeFactory.any()

    def visit_param_spec(self, t):
        return TypeFactory.any()

    def visit_parameters(self, t):
        return TypeFactory.product(*self.translate_types(t.arg_types))

    def visit_type_var_tuple(self, t):
        return TypeFactory.unknown(str(t))

    def visit_partial_type(self, t):
        return TypeFactory.unknown(str(t))

    def visit_unpack_type(self, t):
        return TypeFactory.unknown(str(t))

    def visit_callable_type(self, t):
        if t.param_spec():
            args = None
        else:
            args = TypeFactory.product(*self.translate_types(t.arg_types))
        return TypeFactory.callable(args, t.ret_type.accept(self))

    def visit_tuple_type(self, t):
        return TypeFactory.product(*self.translate_types(t.items))

    def visit_typeddict_type(self, t):
        return TypeFactory.unknown(str(t))

    def visit_literal_type(self, t):
        return TypeFactory.literal(repr(t.value_repr()))

    def visit_union_type(self, t):
        return TypeFactory.sum(*self.translate_types(t.items))

    def translate_types(self, types: Iterable[Type]):
        return [t.accept(self) for t in types]

    def visit_overloaded(self, t: Overloaded) -> Type:
        items: list[CallableType] = []
        for item in t.items:
            new = item.accept(self)
            assert isinstance(new, CallableType)  # type: ignore[misc]
            items.append(new)
        return Overloaded(items=items)

    def visit_type_type(self, t):
        return TypeFactory.callable(None, t.item.accept(self))

    def visit_type_alias_type(self, t):
        # This method doesn't have a default implementation for type translators,
        # because type aliases are special: some information is contained in the
        # TypeAlias node, and we normally don't generate new nodes. Every subclass
        # must implement this depending on its semantics.
        if t.alias is not None:
            unrolled, recursed = t._partial_expansion()
            return unrolled.accept(self)
        return TypeFactory.unknown(str(t))



def encodeType(type: Type | None, logger: "logging.Logger") -> MTypeInfo | None:
    if type is None:
        return None
    try:
        typed = type.accept(Translator())
        result = type.serialize()
        if isinstance(result, str):
            return MTypeInfo(raw=result, data=result, type=typed, id=str(typed))
        else:
            return MTypeInfo(
                raw=str(type),
                data=json.loads(json.dumps(result)),
                type=typed,
                id=str(typed),
            )
    except Exception as ex:
        logger.error(f"Failed to encode type {type}.", exc_info=ex)
        return None


class TypeEnricher(Enricher):
    def __init__(
        self, server: "PackageMypyServer", logger: "logging.Logger | None" = None
    ) -> None:
        super().__init__()
        self.server = server
        self.logger = (
            logger.getChild("type-enrich")
            if logger is not None
            else logging.getLogger("type-enrich")
        )

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
                        assert not isinstance(item, State), "Function entry should not get a state (only for modules)"

                        if item:
                            type = item[0].type
                            func.type = encodeType(type, self.logger)
                            if isinstance(type, CallableType):
                                func.returnType = encodeType(type.ret_type, self.logger)
                                for para in func.parameters:
                                    if para.name not in type.arg_names:
                                        continue
                                    typara = type.argument_by_name(para.name)
                                    para.type = encodeType(typara.typ if typara else None, self.logger)
                    case AttributeEntry() as attr:
                        item = self.server.element(attr)
                        assert not isinstance(item, State), "Attribute entry should not get a state (only for modules)"
                        if item:
                            attrType = None
                            if attr.property:
                                type = item[0].type
                                if isinstance(type, CallableType):
                                    attrType = encodeType(type.ret_type, self.logger)
                            attr.type = attrType or encodeType(
                                item[0].type, self.logger
                            )
            except Exception as ex:
                self.logger.error(f"Failed to enrich entry {entry.id}.", exc_info=ex)
