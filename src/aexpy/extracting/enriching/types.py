import ast
import base64
import json
import logging
from ast import NodeVisitor
from typing import Iterable, Optional, override

import mypy
from mypy import find_sources
from mypy.build import State
from mypy.dmypy_server import Server
from mypy.infer import infer_function_type_arguments
from mypy.nodes import (ARG_NAMED, ARG_NAMED_OPT, ARG_POS, ARG_STAR, ARG_STAR2,
                        AssignmentStmt, CallExpr, Context, Expression,
                        FuncBase, FuncDef, MemberExpr, MypyFile, NameExpr,
                        Node, RefExpr, ReturnStmt, SymbolNode, SymbolTable,
                        SymbolTableNode, TypeInfo, Var)
from mypy.options import Options
from mypy.traverser import TraverserVisitor
from mypy.types import (AnyType, CallableArgument, CallableType, DeletedType,
                        EllipsisType, ErasedType, Instance, LiteralType,
                        NoneTyp, NoneType, Overloaded, Parameters,
                        ParamSpecType, PartialType, PlaceholderType,
                        RawExpressionType, SyntheticTypeVisitor, TupleType,
                        Type, TypeAliasType, TypedDictType, TypeList,
                        TypeOfAny, TypeStrVisitor, TypeType, TypeVarTupleType,
                        TypeVarType, TypeVisitor, UnboundType, UninhabitedType,
                        UnionType, UnpackType, deserialize_type,
                        get_proper_type)
from mypy.util import IdMapper
from mypy.version import __version__

from ...models import ApiDescription
from ...models import typing as mtyping
from ...models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                   FunctionEntry, ModuleEntry, Parameter,
                                   ParameterKind)
from ...models.typing import TypeFactory
from ..third.mypyserver import PackageMypyServer
from . import Enricher, clearSrc


class Translator:
    def accept(self, /, t: Type) -> mtyping.TypeType:
        if isinstance(t, LiteralType):
            return self.visit_literal_type(t)
        elif isinstance(t, TypeAliasType):
            return self.visit_type_alias_type(t)
        elif isinstance(t, TypeType):
            return self.visit_type_type(t)
        elif isinstance(t, UnionType):
            return self.visit_union_type(t)
        elif isinstance(t, TupleType):
            return self.visit_tuple_type(t)
        elif isinstance(t, UnpackType):
            return self.visit_unpack_type(t)
        elif isinstance(t, Overloaded):
            return self.visit_overloaded(t)
        elif isinstance(t, Instance):
            return self.visit_instance(t)
        elif isinstance(t, AnyType):
            return self.visit_any(t)
        elif isinstance(t, NoneType):
            return self.visit_none_type(t)
        elif isinstance(t, UninhabitedType):
            return self.visit_uninhabited_type(t)
        elif isinstance(t, UnboundType):
            return self.visit_unbound_type(t)
        elif isinstance(t, TypeVarType):
            return self.visit_type_var(t)
        elif isinstance(t, CallableType):
            return self.visit_callable_type(t)
        elif isinstance(t, Parameters):
            return self.visit_parameters(t)
        elif isinstance(t, TupleType):
            return self.visit_tuple_type(t)
        elif isinstance(t, ParamSpecType):
            return self.visit_param_spec(t)
        elif isinstance(t, PartialType):
            return self.visit_partial_type(t)
        else:
            return TypeFactory.unknown(str(t))

    def visit_unbound_type(self, /, t: UnboundType):
        return TypeFactory.unknown(str(t))

    def visit_any(self, /, t: AnyType):
        return TypeFactory.any()

    def visit_none_type(self, /, t: NoneType):
        return TypeFactory.none()

    def visit_uninhabited_type(self, /, t: UninhabitedType):
        return TypeFactory.none()

    def visit_instance(self, /, t: Instance):
        last_known_value: mtyping.LiteralType | None = None
        if t.last_known_value is not None:
            raw_last_known_value = self.accept(t.last_known_value)
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

    def visit_type_var(self, /, t):
        return TypeFactory.any()

    def visit_param_spec(self, /, t):
        return TypeFactory.any()

    def visit_parameters(self, /, t: Parameters):
        return TypeFactory.product(*self.translate_types(t.arg_types))

    def visit_partial_type(self, /, t):
        return TypeFactory.unknown(str(t))

    def visit_unpack_type(self, /, t: UnpackType):
        return TypeFactory.unknown(str(t))

    def visit_callable_type(self, /, t: CallableType):
        if t.param_spec():
            args = None
        else:
            args = TypeFactory.product(*self.translate_types(t.arg_types))
        return TypeFactory.callable(args, self.accept(t.ret_type))

    def visit_tuple_type(self, /, t: TupleType):
        return TypeFactory.product(*self.translate_types(t.items))

    def visit_literal_type(self, /, t: LiteralType):
        return TypeFactory.literal(repr(t.value_repr()))

    def visit_union_type(self, /, t: UnionType):
        return TypeFactory.sum(*self.translate_types(t.items))

    def translate_types(self, /, types: Iterable[Type]):
        return [self.accept(t) for t in types]

    def visit_overloaded(self, /, t: Overloaded):
        items: list[mtyping.CallableType] = []
        for item in t.items:
            new = self.accept(item)
            assert isinstance(new, mtyping.CallableType)  # type: ignore[misc]
            items.append(new)
        return TypeFactory.sum(*items)

    def visit_type_type(self, /, t: TypeType):
        return TypeFactory.callable(None, self.accept(t.item))

    def visit_type_alias_type(self, /, t: TypeAliasType):
        # This method doesn't have a default implementation for type translators,
        # because type aliases are special: some information is contained in the
        # TypeAlias node, and we normally don't generate new nodes. Every subclass
        # must implement this depending on its semantics.
        if t.alias is not None:
            unrolled, recursed = t._partial_expansion()
            return self.accept(unrolled)
        return TypeFactory.unknown(str(t))


def encodeType(type: Type | None, logger: logging.Logger) -> mtyping.TypeType | None:
    if type is None:
        return None
    try:
        typed = Translator().accept(type)
        result = type.serialize()
        typed.id = str(typed)
        if isinstance(result, str):
            typed.raw = result
            typed.data = result
        else:
            typed.raw = str(type)
            typed.data = json.loads(json.dumps(result))
        return typed
    except Exception:
        logger.error(f"Failed to encode type {type}.", exc_info=True)
        return None


class TypeEnricher(Enricher):
    def __init__(
        self, /, server: PackageMypyServer, logger: logging.Logger | None = None
    ) -> None:
        super().__init__()
        self.server = server
        self.logger = (
            logger.getChild("type-enrich")
            if logger is not None
            else logging.getLogger("type-enrich")
        )

    @override
    def enrich(self, /, api):
        for entry in api:
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
                                func.returnType = encodeType(type.ret_type, self.logger)
                                for para in func.parameters:
                                    if para.name not in type.arg_names:
                                        continue
                                    typara = type.argument_by_name(para.name)
                                    para.type = encodeType(
                                        typara.typ if typara else None, self.logger
                                    )
                    case AttributeEntry() as attr:
                        item = self.server.element(attr)
                        if item:
                            attrType = None
                            if attr.property:
                                type = item[0].type
                                if isinstance(type, CallableType):
                                    attrType = encodeType(type.ret_type, self.logger)
                            attr.type = attrType or encodeType(
                                item[0].type, self.logger
                            )
            except Exception:
                self.logger.error(f"Failed to enrich entry {entry.id}.", exc_info=True)
