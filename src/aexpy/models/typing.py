import inspect
from dataclasses import dataclass, field
from typing import Callable

from aexpy.utils import getObjectId


@dataclass
class Type:
    schema: "str" = ""


@dataclass
class NoneType(Type):
    def __post_init__(self):
        self.schema = "none"

    def __repr__(self) -> str:
        return "none"


@dataclass
class AnyType(Type):
    def __post_init__(self):
        self.schema = "any"

    def __repr__(self) -> str:
        return "any"


@dataclass
class UnknownType(Type):
    message: "str" = ""

    def __post_init__(self):
        self.schema = "unknown"

    def __repr__(self) -> str:
        return f"unknown({self.message})"


@dataclass
class LiteralType(Type):
    value: str = ""

    def __post_init__(self):
        self.schema = "literal"

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass
class ClassType(Type):
    id: "str" = ""

    def __post_init__(self):
        self.schema = "class"

    def __repr__(self) -> str:
        return self.id


@dataclass
class SumType(Type):
    types: "list[Type]" = field(default_factory=list)

    def __post_init__(self):
        self.schema = "sum"

    def __repr__(self) -> str:
        return f"[{' | '.join(repr(t) for t in self.types)}]"


@dataclass
class ProductType(Type):
    types: "list[Type]" = field(default_factory=list)

    def __post_init__(self):
        self.schema = "product"

    def __repr__(self) -> str:
        return f"({' , '.join(repr(t) for t in self.types)})"


@dataclass
class CallableType(Type):
    args: "Type" = field(default_factory=UnknownType)
    ret: "Type" = field(default_factory=UnknownType)

    def __post_init__(self):
        self.schema = "callable"

    def __repr__(self) -> str:
        return f"{repr(self.args)} -> {repr(self.ret)}"


@dataclass
class GenericType(Type):
    base: "Type" = field(default_factory=UnknownType)
    vars: "list[Type]" = field(default_factory=list)

    def __post_init__(self):
        self.schema = "generic"

    def __repr__(self) -> str:
        return f"{repr(self.base)}<{' , '.join(repr(t) for t in self.vars)}>"


class TypeFactory:
    @classmethod
    def list(cls, type: "Type | None" = None) -> "GenericType":
        return cls.generic(cls.fromType(list), type or cls.unknown())

    @classmethod
    def dict(cls, key: "Type | None" = None, value: "Type | None" = None) -> "GenericType":
        return cls.generic(cls.fromType(dict), key or cls.unknown(), value or cls.unknown())

    @classmethod
    def set(cls, type: "Type | None" = None) -> "GenericType":
        return cls.generic(cls.fromType(set), type or cls.unknown())

    @classmethod
    def sum(cls, *types: "Type") -> "SumType":
        return SumType(types=types)

    @classmethod
    def product(cls, *types: "Type") -> "ProductType":
        return ProductType(types=types)

    @classmethod
    def generic(cls, base: "Type", *vars: "Type") -> "GenericType":
        return GenericType(base=base, vars=vars)

    @classmethod
    def callable(cls, args: "ProductType | None" = None, ret: "Type | None" = None) -> "CallableType":
        return CallableType(args=args or cls.unknown(), ret=ret or cls.unknown())

    @classmethod
    def fromType(cls, typeCls) -> "ClassType":
        return ClassType(id=getObjectId(typeCls))

    @classmethod
    def literal(cls, value: str) -> "LiteralType":
        return LiteralType(value=value)

    @classmethod
    def any(cls) -> "AnyType":
        return AnyType()

    @classmethod
    def unknown(cls, message: "str" = "") -> "UnknownType":
        return UnknownType(message=message)

    @classmethod
    def none(cls) -> "NoneType":
        return NoneType()

    @classmethod
    def fromInstance(cls, instance) -> "ClassType | NoneType":
        if instance is None:
            return cls.none()
        return cls.fromType(type(instance))


def loadType(entry: "dict | None") -> "Type | None":
    if entry is None:
        return None
    schema = entry.pop("schema")
    data: dict = entry
    if schema == "none":
        return NoneType(**data)
    elif schema == "any":
        return AnyType(**data)
    elif schema == "unknown":
        return UnknownType(**data)
    elif schema == "class":
        return ClassType(**data)
    elif schema == "literal":
        return LiteralType(**data)
    elif schema == "sum":
        data["types"] = [loadType(t) for t in data["types"]]
        return SumType(**data)
    elif schema == "product":
        data["types"] = [loadType(t) for t in data["types"]]
        return ProductType(**data)
    elif schema == "callable":
        data["args"] = loadType(data["args"])
        data["ret"] = loadType(data["ret"])
        return CallableType(**data)
    elif schema == "generic":
        data["base"] = loadType(data["base"])
        data["vars"] = [loadType(v) for v in data["vars"]]
        return GenericType(**data)


def copyType(type: "Type") -> "Type":
    if isinstance(type, NoneType):
        return NoneType()
    elif isinstance(type, AnyType):
        return AnyType()
    elif isinstance(type, UnknownType):
        return UnknownType(message=type.message)
    elif isinstance(type, LiteralType):
        return LiteralType(value=type.value)
    elif isinstance(type, ClassType):
        return ClassType(id=type.id)
    elif isinstance(type, SumType):
        return SumType(types=[copyType(t) for t in type.types])
    elif isinstance(type, ProductType):
        return ProductType(types=[copyType(t) for t in type.types])
    elif isinstance(type, CallableType):
        return CallableType(args=copyType(type.args), ret=copyType(type.ret))
    elif isinstance(type, GenericType):
        return GenericType(base=copyType(type.base), vars=[copyType(v) for v in type.vars])
    else:
        raise TypeError(f"Unknown type {type}")
