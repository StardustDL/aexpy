from typing import Literal, Annotated
from pydantic import BaseModel, Field
from aexpy.utils import getObjectId

type TypeType = "NoneType | AnyType | UnknownType | LiteralType | ClassType | ProductType | SumType | CallableType | GenericType"

class Type(BaseModel):
    pass


class NoneType(Type):
    form: Literal["none"] = "none"

    def __repr__(self):
        return "none"


class AnyType(Type):
    form: Literal["any"] = "any"

    def __repr__(self):
        return "any"


class UnknownType(Type):
    form: Literal["unknown"] = "unknown"
    message: str = ""

    def __repr__(self):
        return f"unknown({self.message})"


class LiteralType(Type):
    form: Literal["literal"] = "literal"
    value: str = ""

    def __repr__(self):
        return repr(self.value)


class ClassType(Type):
    form: Literal["class"] = "class"
    id: str = ""

    def __repr__(self):
        return self.id


class SumType(Type):
    form: Literal["sum"] = "sum"
    types: list[TypeType] = []

    def __repr__(self):
        return f"[{' | '.join(repr(t) for t in self.types)}]"


class ProductType(Type):
    form: Literal["product"] = "product"
    types: list[TypeType] = []

    def __repr__(self):
        return f"({' , '.join(repr(t) for t in self.types)})"


class CallableType(Type):
    form: Literal["callable"] = "callable"
    args: TypeType = UnknownType()
    ret: TypeType = UnknownType()

    def __repr__(self):
        return f"{repr(self.args)} -> {repr(self.ret)}"


class GenericType(Type):
    form: Literal["generic"] = "generic"
    base: TypeType = UnknownType()
    vars: list[TypeType] = []

    def __repr__(self):
        return f"{repr(self.base)}<{' , '.join(repr(t) for t in self.vars)}>"


class TypeFactory:
    @classmethod
    def list(cls, type: TypeType | None = None):
        return cls.generic(cls.fromType(list), type or cls.unknown())

    @classmethod
    def dict(cls, key: TypeType | None = None, value: TypeType | None = None):
        return cls.generic(
            cls.fromType(dict), key or cls.unknown(), value or cls.unknown()
        )

    @classmethod
    def set(cls, type: TypeType | None = None):
        return cls.generic(cls.fromType(set), type or cls.unknown())

    @classmethod
    def sum(cls, *types: TypeType):
        return SumType(types=list(types))

    @classmethod
    def product(cls, *types: TypeType):
        return ProductType(types=list(types))

    @classmethod
    def generic(cls, base: TypeType, *vars: TypeType):
        return GenericType(base=base, vars=list(vars))

    @classmethod
    def callable(cls, args: ProductType | None = None, ret: TypeType | None = None):
        return CallableType(args=args or cls.unknown(), ret=ret or cls.unknown())

    @classmethod
    def fromType(cls, typeCls):
        return ClassType(id=getObjectId(typeCls))

    @classmethod
    def literal(cls, value: str):
        return LiteralType(value=value)

    @classmethod
    def any(cls):
        return AnyType()

    @classmethod
    def unknown(cls, message: str = ""):
        return UnknownType(message=message)

    @classmethod
    def none(cls):
        return NoneType()

    @classmethod
    def fromInstance(cls, instance):
        if instance is None:
            return cls.none()
        return cls.fromType(type(instance))


def loadType(entry: dict | None) -> TypeType | None:
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


def copyType(type: TypeType) -> TypeType:
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
        return GenericType(
            base=copyType(type.base), vars=[copyType(v) for v in type.vars]
        )
    else:
        raise TypeError(f"Unknown type {type}")
