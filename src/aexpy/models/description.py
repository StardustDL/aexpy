from dataclasses import dataclass, field, asdict
from datetime import timedelta
from enum import Enum
from typing import Any


@dataclass
class Location:
    file: "str" = ""
    line: "int" = -1
    module: "str" = ""

    def __str__(self):
        return f"{self.file}:{self.line}:{self.module}"


@dataclass
class ApiEntry:
    name: "str" = ""
    id: "str" = ""
    docs: "str" = field(default="", repr=False)
    comments: "str" = field(default="", repr=False)
    src: "str" = field(default="", repr=False)
    location: "Location" = field(default_factory=Location)


@dataclass
class CollectionEntry(ApiEntry):
    members: "dict[str, str]" = field(default_factory=dict)
    annotations: "dict[str, str]" = field(default_factory=dict)


@dataclass
class ItemEntry(ApiEntry):
    bound: bool = False


class SpecialKind(Enum):
    Unknown = 0
    Empty = 1
    External = 2


@dataclass
class SpecialEntry(ApiEntry):
    kind: "SpecialKind" = SpecialKind.Unknown
    data: "str" = ""


@dataclass
class ModuleEntry(CollectionEntry):
    pass


@dataclass
class ClassEntry(CollectionEntry):
    bases: "list[str]" = field(default_factory=list)
    mro: "list[str]" = field(default_factory=list)


@dataclass
class AttributeEntry(ItemEntry):
    type: "str" = ""
    typeData: "dict" = field(default_factory=dict)
    rawType: "str" = ""


class ParameterKind(Enum):
    Positional = 0
    PositionalOrKeyword = 1
    VarPositional = 2
    Keyword = 3
    VarKeyword = 4
    VarKeywordCandidate = 5


@dataclass
class Parameter:
    kind: "ParameterKind" = ParameterKind.PositionalOrKeyword
    name: "str" = ""
    annotation: "str" = ""
    default: "str | None" = None
    """Default value. None for variable default value."""
    optional: "bool" = False
    source: "str" = ""

    @property
    def isKeyword(self):
        return self.kind in {ParameterKind.Keyword, ParameterKind.PositionalOrKeyword, ParameterKind.VarKeywordCandidate}

    @property
    def isPositional(self):
        return self.kind in {ParameterKind.Positional, ParameterKind.PositionalOrKeyword}

    @property
    def isVar(self):
        return self.kind in {ParameterKind.VarKeyword, ParameterKind.VarPositional}


@dataclass
class FunctionEntry(ItemEntry):
    returnAnnotation: "str" = ""
    parameters: "list[Parameter]" = field(default_factory=list)
    annotations: "dict[str, str]" = field(default_factory=dict)

    def getVarPositionalParameter(self) -> "Parameter | None":
        items = [x for x in self.parameters if x.kind ==
                 ParameterKind.VarPositional]
        if len(items) > 0:
            return items[0]
        return None

    def getVarKeywordParameter(self) -> "Parameter | None":
        items = [x for x in self.parameters if x.kind ==
                 ParameterKind.VarKeyword]
        if len(items) > 0:
            return items[0]
        return None


def jsonifyEntry(x):
    assert isinstance(x, ApiEntry)
    if isinstance(x, FunctionEntry):
        return {
            "schema": "func",
            **asdict(x)
        }
    elif isinstance(x, AttributeEntry):
        return {
            "schema": "attr",
            **asdict(x)
        }
    elif isinstance(x, ClassEntry):
        return {
            "schema": "class",
            **asdict(x)
        }
    elif isinstance(x, ModuleEntry):
        return {
            "schema": "module",
            **asdict(x)
        }
    elif isinstance(x, SpecialEntry):
        return {
            "schema": "special",
            **asdict(x)
        }


def loadEntry(entry: "dict") -> ApiEntry:
    schema = entry.pop("schema")
    data: dict = entry
    locationData: dict = data.pop("location")
    if schema == "attr":
        binded = AttributeEntry(**data)
    elif schema == "module":
        binded = ModuleEntry(**data)
    elif schema == "class":
        binded = ClassEntry(**data)
    elif schema == "func":
        paras = data.pop("parameters")
        bindedParas = []
        for para in paras:
            kind = ParameterKind(para.pop("kind"))
            bindedParas.append(Parameter(kind=kind, **para))
        binded = FunctionEntry(parameters=bindedParas, **data)
    elif schema == "special":
        kind = SpecialKind(data.pop("kind"))
        binded = SpecialEntry(kind=kind, **data)
    assert isinstance(binded, ApiEntry)
    binded.location = Location(**locationData)
    return binded
