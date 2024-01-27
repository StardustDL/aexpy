from typing import TYPE_CHECKING, Mapping, Literal, Annotated
from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType

if TYPE_CHECKING:
    type RecursiveType = str | Mapping[str, RecursiveType]
else:
    RecursiveType = TypeAliasType("RecursiveType", "str | Mapping[str, RecursiveType]")

type T = Annotated["B | C", Field(discriminator='s')]

class A(BaseModel):
    sub: list[T] | None = None

class B(A):
    s: Literal["b"] = "b"

class C(A):
    s: Literal["c"] = "c"

class Model(BaseModel):
    value: RecursiveType | None

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

class BCDEF(BaseModel):
    base: Annotated[TypeType, Field(discriminator="form")] = UnknownType()


if __name__ == "__main__":
    print(GenericType(vars=[UnknownType()]).model_dump())
    BCDEF.mro