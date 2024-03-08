import inspect
from enum import IntEnum, IntFlag
from pathlib import Path
from typing import Any, Dict, List, Literal, Set, Union

from pydantic import BaseModel


class Distribution(BaseModel):
    rootPath: Union[Path, None] = None
    topModules: List[str] = []


class Location(BaseModel):
    file: str = ""
    line: int = -1
    module: str = ""


class ApiEntry(BaseModel):
    name: str = ""
    id: str = ""
    alias: List[str] = []
    docs: str = ""
    comments: str = ""
    src: str = ""
    location: Union[Location, None] = None
    private: bool = False
    deprecated: bool = False
    parent: str = ""
    data: Dict[str, Any] = {}


class CollectionEntry(ApiEntry):
    members: Dict[str, str] = {}
    slots: Set[str] = set()
    annotations: Dict[str, str] = {}


class ItemScope(IntEnum):
    Static = 0
    Class = 1
    Instance = 2


class ItemEntry(ApiEntry):
    scope: ItemScope = ItemScope.Static


class SpecialKind(IntEnum):
    Unknown = 0
    Empty = 1
    External = 2


class SpecialEntry(ApiEntry):
    form: Literal["special"] = "special"
    kind: SpecialKind = SpecialKind.Unknown


class ModuleEntry(CollectionEntry):
    form: Literal["module"] = "module"


class ClassFlag(IntFlag):
    Empty = 0
    Abstract = 1 << 0
    Final = 1 << 1
    Generic = 1 << 2
    Dataclass = 1 << 10


class ClassEntry(CollectionEntry):
    form: Literal["class"] = "class"

    bases: List[str] = []
    subclasses: List[str] = []
    abcs: List[str] = []
    mros: List[str] = []
    flags: ClassFlag = ClassFlag.Empty


class AttributeEntry(ItemEntry):
    form: Literal["attr"] = "attr"

    rawType: str = ""
    annotation: str = ""
    property: bool = False


class ParameterKind(IntEnum):
    Positional = 0
    PositionalOrKeyword = 1
    VarPositional = 2
    Keyword = 3
    VarKeyword = 4
    VarKeywordCandidate = 5


class Parameter(BaseModel):
    kind: ParameterKind = ParameterKind.PositionalOrKeyword
    name: str = ""
    annotation: str = ""
    default: Union[str, None] = None
    """Default value. None for variable default value."""
    optional: bool = False
    source: str = ""


class FunctionFlag(IntFlag):
    Empty = 0
    Abstract = 1 << 0
    Final = 1 << 1
    Generic = 1 << 2
    Override = 1 << 10
    Async = 1 << 11
    TransmitKwargs = 1 << 20


class FunctionEntry(ItemEntry):
    form: Literal["func"] = "func"

    returnAnnotation: str = ""
    parameters: List[Parameter] = []
    annotations: Dict[str, str] = {}
    callers: List[str] = []
    callees: List[str] = []
    flags: FunctionFlag = FunctionFlag.Empty


def isFunction(obj):
    return (
        inspect.isroutine(obj)
        or inspect.isfunction(obj)
        or inspect.ismethod(obj)
        or inspect.iscoroutinefunction(obj)
        or inspect.isasyncgenfunction(obj)
        or inspect.isgeneratorfunction(obj)
    )


def getModuleName(obj):
    module = inspect.getmodule(obj)
    if module:
        return module.__name__
    else:
        return str(getattr(obj, "__module__", ""))


def getObjectId(obj) -> "str":
    if inspect.ismodule(obj):
        return obj.__name__

    moduleName = getModuleName(obj)
    qualname = getattr(obj, "__qualname__", "")
    if not qualname:
        qualname = getattr(obj, "__name__", "")

    if inspect.isclass(obj):
        if not qualname:
            qualname = f"<class ({type(obj)})>"
    elif isFunction(obj):
        if not qualname:
            qualname = f"<function ({type(obj)})>"
    else:
        if not qualname:
            qualname = f"<instance ({type(obj)})>"

    if moduleName:
        return f"{moduleName}.{qualname}"
    else:
        return qualname


def isLocal(name: str) -> bool:
    # function closure, or other special cases
    return "<locals>" in name
