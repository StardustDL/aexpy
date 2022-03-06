from dataclasses import asdict, dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any

TRANSFER_BEGIN = "AEXPY_TRANSFER_BEGIN"
EXTERNAL_ENTRYID = "$external$"


@dataclass
class TypeInfo:
    type: "str" = ""
    data: "dict" = field(default_factory=dict)


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
    alias: "list[str]" = field(default_factory=list)
    docs: "str" = field(default="", repr=False)
    comments: "str" = field(default="", repr=False)
    src: "str" = field(default="", repr=False)
    location: "Location | None" = None


@dataclass
class CollectionEntry(ApiEntry):
    members: "dict[str, str]" = field(default_factory=dict)
    annotations: "dict[str, str]" = field(default_factory=dict)

    @property
    def aliasMembers(self):
        if not hasattr(self, "_aliasMembers"):
            self._aliasMembers = {
                k: v for k, v in self.members.items() if v != f"{self.id}.{k}"}
        return self._aliasMembers


@dataclass
class ItemEntry(ApiEntry):
    bound: "bool" = False
    type: "TypeInfo | None" = None


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
    abcs: "list[str]" = field(default_factory=list)
    mro: "list[str]" = field(default_factory=list)
    slots: "list[str]" = field(default_factory=list)


@dataclass
class AttributeEntry(ItemEntry):
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
    type: "TypeInfo | None" = None

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
    returnType: "TypeInfo | None" = None

    def getParameter(self, name: str) -> "Parameter | None":
        for p in self.parameters:
            if p.name == name:
                return p

    def position(self, parameter: "Parameter") -> "int | None":
        try:
            return self.positionals.index(parameter)
        except:
            return None

    @property
    def positionals(self):
        return [x for x in self.parameters if x.isPositional]

    @property
    def keywords(self):
        return [x for x in self.parameters if x.isKeyword]

    @property
    def candidates(self):
        return [x for x in self.parameters if x.kind == ParameterKind.VarKeywordCandidate]

    @property
    def varPositional(self) -> "Parameter | None":
        items = [x for x in self.parameters if x.kind ==
                 ParameterKind.VarPositional]
        if len(items) > 0:
            return items[0]
        return None

    @property
    def varKeyword(self) -> "Parameter | None":
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


def loadEntry(entry: "dict | None") -> "ApiEntry | None":
    if entry is None:
        return None
    schema = entry.pop("schema")
    data: dict = entry
    if schema == "attr":
        type = data.pop("type")
        type = TypeInfo(**type) if type is not None else None
        binded = AttributeEntry(type=type, **data)
    elif schema == "module":
        binded = ModuleEntry(**data)
    elif schema == "class":
        binded = ClassEntry(**data)
    elif schema == "func":
        type = data.pop("type")
        type = TypeInfo(**type) if type is not None else None
        returnType = data.pop("returnType")
        returnType = TypeInfo(**returnType) if returnType is not None else None
        paras = data.pop("parameters")
        bindedParas = []
        for para in paras:
            kind = ParameterKind(para.pop("kind"))
            paratype = para.pop("type")
            paratype = TypeInfo(**paratype) if paratype is not None else None
            bindedParas.append(Parameter(kind=kind, type=paratype, **para))
        binded = FunctionEntry(parameters=bindedParas,
                               type=type, returnType=returnType, **data)
    elif schema == "special":
        kind = SpecialKind(data.pop("kind"))
        binded = SpecialEntry(kind=kind, **data)
    assert isinstance(binded, ApiEntry)
    if "location" in data and data["location"] is not None:
        location = Location(**data["location"])
        binded.location = location
    return binded
