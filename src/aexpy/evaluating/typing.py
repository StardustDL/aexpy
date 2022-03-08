from temp.type.models import UnknownType
from ..models.typing import Type, ClassType, SumType, ProductType, CallableType, GenericType, AnyType, NoneType
from aexpy.utils import getObjectId


class TypeCompatibilityChecker:
    def isSubclass(self, a: "ClassType", b: "ClassType") -> bool:
        return a.id == b.id or b.id == getObjectId(object)

    def isClassCompatibleTo(self, a: "ClassType", b: "Type"):

        match b:
            case ClassType() as cls:
                return self.isSubclass(a, cls)
            case SumType() as sum:
                return any(self.isClassCompatibleTo(a, t) for t in sum.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False

    def isSumCompatibleTo(self, a: "SumType", b: "Type"):

        match b:
            case SumType() as sum:
                return all(self.isCompatibleTo(t, sum) for t in a.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False

    def isProductCompatibleTo(self, a: "ProductType", b: "Type"):

        match b:
            case ProductType() as prod:
                return len(a.types) == len(prod.types) and all(self.isCompatibleTo(t, p) for t, p in zip(a.types, prod.types))
            case SumType() as sum:
                return any(self.isClassCompatibleTo(a, t) for t in sum.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False

    def isCallableCompatibleTo(self, a: "CallableType", b: "Type"):

        match b:
            case CallableType() as callable:
                return self.isCompatibleTo(callable.args, a.args) and self.isCompatibleTo(a.ret, callable.ret)
            case SumType() as sum:
                return any(self.isClassCompatibleTo(a, t) for t in sum.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False

    def isGenericCompatibleTo(self, a: "GenericType", b: "Type"):

        match b:
            case GenericType() as generic:
                return len(a.vars) == len(generic.vars) and self.isCompatibleTo(a.base, generic.base) and all(self.isCompatibleTo(t, g) for t, g in zip(a.vars, generic.vars))
            case SumType() as sum:
                return any(self.isClassCompatibleTo(a, t) for t in sum.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False

    def isAnyCompatibleTo(self, a: "AnyType", b: "Type") -> bool:

        match b:
            case SumType() as sum:
                return any(self.isClassCompatibleTo(a, t) for t in sum.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False

    def isNoneCompatibleTo(self, a: "NoneType", b: "Type") -> bool:

        match b:
            case NoneType():
                return True
            case SumType() as sum:
                return any(self.isClassCompatibleTo(a, t) for t in sum.types)
            case AnyType():
                return True
            case UnknownType():
                return True
            case _:
                return False
    
    def isUnknownCompatibleTo(self, a: "UnknownType", b: "Type") -> bool:
        return True

    def isCompatibleTo(self, a: "Type", b: "Type") -> bool:
        """Return type class a is a subset of type class b, indicating that instance of a can be assign to variable of b."""

        match a:
            case ClassType() as cls:
                return self.isClassCompatibleTo(cls, b)
            case SumType() as sum:
                return self.isSumCompatibleTo(sum, b)
            case ProductType() as prod:
                return self.isProductCompatibleTo(prod, b)
            case CallableType() as callable:
                return self.isCallableCompatibleTo(callable, b)
            case GenericType() as generic:
                return self.isGenericCompatibleTo(generic, b)
            case AnyType():
                return self.isAnyCompatibleTo(a, b)
            case NoneType():
                return self.isNoneCompatibleTo(a, b)
            case UnknownType():
                return self.isUnknownCompatibleTo(a, b)
            case _:
                return False
