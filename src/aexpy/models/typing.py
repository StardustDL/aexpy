from typing import Literal

from pydantic import BaseModel

from ..utils import getObjectId

type TypeType = "NoneType | AnyType | UnknownType | LiteralType | ClassType | ProductType | SumType | CallableType | GenericType"


class Type(BaseModel):
    id: str = ""
    raw: str = ""
    data: dict | str = ""


class NoneType(Type):
    form: Literal["none"] = "none"

    def __str__(self, /):
        return "none"


class AnyType(Type):
    form: Literal["any"] = "any"

    def __str__(self, /):
        return "any"


class UnknownType(Type):
    form: Literal["unknown"] = "unknown"
    message: str = ""

    def __str__(self, /):
        return f"unknown({self.message})"


class LiteralType(Type):
    form: Literal["literal"] = "literal"
    value: str = ""

    def __str__(self, /):
        return str(self.value)


class ClassType(Type):
    form: Literal["class"] = "class"
    id: str = ""

    def __str__(self, /):
        return self.id


class SumType(Type):
    form: Literal["sum"] = "sum"
    types: list[TypeType] = []

    def __str__(self, /):
        return f"[{' | '.join(str(t) for t in self.types)}]"


class ProductType(Type):
    form: Literal["product"] = "product"
    types: list[TypeType] = []

    def __str__(self, /):
        return f"({' , '.join(str(t) for t in self.types)})"


class CallableType(Type):
    form: Literal["callable"] = "callable"
    args: TypeType = UnknownType()
    ret: TypeType = UnknownType()

    def __str__(self, /):
        return f"{str(self.args)} -> {str(self.ret)}"


class GenericType(Type):
    form: Literal["generic"] = "generic"
    base: TypeType = UnknownType()
    vars: list[TypeType] = []

    def __str__(self, /):
        return f"{str(self.base)}<{' , '.join(str(t) for t in self.vars)}>"


class TypeFactory:
    @classmethod
    def list(cls, /, type: TypeType | None = None):
        return cls.generic(cls.fromType(list), type or cls.unknown())

    @classmethod
    def dict(cls, /, key: TypeType | None = None, value: TypeType | None = None):
        return cls.generic(
            cls.fromType(dict), key or cls.unknown(), value or cls.unknown()
        )

    @classmethod
    def set(cls, /, type: TypeType | None = None):
        return cls.generic(cls.fromType(set), type or cls.unknown())

    @classmethod
    def sum(cls, /, *types: TypeType):
        return SumType(types=list(types))

    @classmethod
    def product(cls, /, *types: TypeType):
        return ProductType(types=list(types))

    @classmethod
    def generic(cls, /, base: TypeType, *vars: TypeType):
        return GenericType(base=base, vars=list(vars))

    @classmethod
    def callable(cls, /, args: ProductType | None = None, ret: TypeType | None = None):
        return CallableType(args=args or cls.unknown(), ret=ret or cls.unknown())

    @classmethod
    def fromType(cls, /, typeCls):
        return ClassType(id=getObjectId(typeCls))

    @classmethod
    def literal(cls, /, value: str):
        return LiteralType(value=value)

    @classmethod
    def any(cls, /):
        return AnyType()

    @classmethod
    def unknown(cls, /, message: str = ""):
        return UnknownType(message=message)

    @classmethod
    def none(cls, /):
        return NoneType()

    @classmethod
    def fromInstance(cls, /, instance):
        if instance is None:
            return cls.none()
        return cls.fromType(type(instance))
