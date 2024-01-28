from enum import Enum, IntEnum
from typing import Any, Literal, Annotated, override
from pydantic import BaseModel, Field

from aexpy.utils import isPrivateName

from .typing import TypeType

TRANSFER_BEGIN = "AEXPY_TRANSFER_BEGIN"
EXTERNAL_ENTRYID = "$external$"


class Location(BaseModel):
    file: str = ""
    line: int = -1
    module: str = ""

    def __str__(self):
        return f"{self.file}:{self.line}:{self.module}"


class ApiEntry(BaseModel):
    name: str = ""
    id: str = ""
    alias: list[str] = []
    docs: str = ""
    comments: str = ""
    src: str = ""
    location: Location | None = None
    private: bool = False
    parent: str = ""
    data: dict[str, Any] = {}


class CollectionEntry(ApiEntry):
    members: dict[str, str] = {}
    annotations: dict[str, str] = {}

    @property
    def aliasMembers(self):
        if not hasattr(self, "_aliasMembers"):
            self._aliasMembers = {
                k: v for k, v in self.members.items() if v != f"{self.id}.{k}"
            }
        return self._aliasMembers


class ItemScope(IntEnum):
    Static = 0
    Class = 1
    Instance = 2


class ItemEntry(ApiEntry):
    scope: ItemScope = ItemScope.Static
    type: Annotated[TypeType, Field(discriminator="form")] | None = None


class SpecialKind(IntEnum):
    Unknown = 0
    Empty = 1
    External = 2


class SpecialEntry(ApiEntry):
    form: Literal["special"] = "special"
    kind: SpecialKind = SpecialKind.Unknown


class ModuleEntry(CollectionEntry):
    form: Literal["module"] = "module"


class ClassEntry(CollectionEntry):
    form: Literal["class"] = "class"

    bases: list[str] = []
    abcs: list[str] = []
    mros: list[str] = []
    slots: list[str] = []


class AttributeEntry(ItemEntry):
    form: Literal["attr"] = "attr"

    rawType: str = ""
    annotation: str = ""
    property: bool = False


class ParameterKind(Enum):
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
    default: str | None = None
    """Default value. None for variable default value."""
    optional: bool = False
    source: str = ""
    type: Annotated[TypeType, Field(discriminator="form")] | None = None

    @property
    def isKeyword(self):
        return self.kind in {
            ParameterKind.Keyword,
            ParameterKind.PositionalOrKeyword,
            ParameterKind.VarKeywordCandidate,
        }

    @property
    def isPositional(self):
        return self.kind in {
            ParameterKind.Positional,
            ParameterKind.PositionalOrKeyword,
        }

    @property
    def isVar(self):
        return self.kind in {ParameterKind.VarKeyword, ParameterKind.VarPositional}


class FunctionEntry(ItemEntry):
    form: Literal["func"] = "func"

    returnAnnotation: str = ""
    parameters: list[Parameter] = []
    annotations: dict[str, str] = {}
    returnType: Annotated[TypeType, Field(discriminator="form")] | None = None
    callers: list[str] = []
    callees: list[str] = []
    transmitKwargs: bool = False

    def getParameter(self, name: str):
        for p in self.parameters:
            if p.name == name:
                return p

    def position(self, parameter: Parameter):
        try:
            return self.positionals.index(parameter)
        except:
            return None

    @property
    def positionalOnlys(self):
        return [x for x in self.parameters if x.kind == ParameterKind.Positional]

    @property
    def positionals(self):
        return [x for x in self.parameters if x.isPositional]

    @property
    def keywordOnlys(self):
        return [x for x in self.parameters if x.kind == ParameterKind.Keyword]

    @property
    def keywords(self):
        return [x for x in self.parameters if x.isKeyword]

    @property
    def candidates(self):
        return [
            x for x in self.parameters if x.kind == ParameterKind.VarKeywordCandidate
        ]

    @property
    def varPositional(self):
        items = [x for x in self.parameters if x.kind == ParameterKind.VarPositional]
        if len(items) > 0:
            return items[0]
        return None

    @property
    def varKeyword(self):
        items = [x for x in self.parameters if x.kind == ParameterKind.VarKeyword]
        if len(items) > 0:
            return items[0]
        return None


type ApiEntryType = ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry


def isPrivate(entry: ApiEntry):
    names = [entry.id, *entry.alias]
    for alias in names:
        if not isPrivateName(alias):
            return False
    return True
