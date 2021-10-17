from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List


@dataclass
class Location:
    file: str = ""
    line: str = ""
    module: str = ""


@dataclass
class ApiManifest:
    project: str = ""
    version: str = ""
    python: str = "'"
    rootModule: str = ""


@dataclass
class ApiEntry:
    name: str = ""
    id: str = ""
    doc: str = field(default="", repr=False)
    comments: str = field(default="", repr=False)
    src: str = field(default="", repr=False)
    location: Location = field(default_factory=Location)


@dataclass
class ApiCollection:
    manifest: ApiManifest = field(default_factory=ApiManifest)
    entries: Dict[str, ApiEntry] = field(default_factory=dict)

    def addEntry(self, entry: ApiEntry) -> None:
        self.entries[entry.id] = entry

    @property
    def names(self) -> Dict[str, List[ApiEntry]]:
        if hasattr(self, "_names"):
            return self._names
        self._names: Dict[str, List[ApiEntry]] = {}
        for item in self.entries.values():
            if item.name in self._names:
                self._names[item.name].append(item)
            else:
                self._names[item.name] = [item]
        return self._names

    @property
    def modules(self) -> Dict[str, "ModuleEntry"]:
        if hasattr(self, "_modules"):
            return self._modules
        self._modules = {
            k: v for k, v in self.entries.items() if isinstance(v, ModuleEntry)
        }
        return self._modules

    @property
    def classes(self) -> Dict[str, "ClassEntry"]:
        if hasattr(self, "_classes"):
            return self._classes
        self._classes = {
            k: v for k, v in self.entries.items() if isinstance(v, ClassEntry)
        }
        return self._modules

    @property
    def funcs(self) -> Dict[str, "FunctionEntry"]:
        if hasattr(self, "_funcs"):
            return self._funcs
        self._funcs = {
            k: v for k, v in self.entries.items() if isinstance(v, FunctionEntry)
        }
        return self._funcs

    @property
    def fields(self) -> Dict[str, "FieldEntry"]:
        if hasattr(self, "_fields"):
            return self._fields
        self._fields = {
            k: v for k, v in self.entries.items() if isinstance(v, FieldEntry)
        }
        return self._fields


@dataclass
class CollectionEntry(ApiEntry):
    members: Dict[str, str] = field(default_factory=dict)


@dataclass
class ItemEntry(ApiEntry):
    bound: bool = False


class SpecialKind(Enum):
    Unknown = 0
    Empty = 1
    External = 2


@dataclass
class SpecialEntry(ApiEntry):
    kind: SpecialKind = SpecialKind.Unknown
    data: str = ""


@dataclass
class ModuleEntry(CollectionEntry):
    pass


@dataclass
class ClassEntry(CollectionEntry):
    bases: List[str] = field(default_factory=list)


@dataclass
class FieldEntry(ItemEntry):
    type: str = ""


class ParameterKind(Enum):
    Positional = 0
    PositionalOrKeyword = 1
    VarPositional = 2
    Keyword = 3
    VarKeyword = 4
    VarKeywordCandidate = 5


@dataclass
class Parameter:
    kind: ParameterKind = ParameterKind.PositionalOrKeyword
    name: str = ""
    type: str = ""
    default: Optional[str] = None  # None for variable default value
    optional: bool = False

    def isKeyword(self):
        return self.kind in {ParameterKind.Keyword, ParameterKind.PositionalOrKeyword, ParameterKind.VarKeywordCandidate}

    def isPositional(self):
        return self.kind in {ParameterKind.Positional, ParameterKind.PositionalOrKeyword}
    
    def isVar(self):
        return self.kind in {ParameterKind.VarKeyword, ParameterKind.VarPositional}


@dataclass
class FunctionEntry(ItemEntry):
    returnType: str = ""
    parameters: List[Parameter] = field(default_factory=list)

    def getVarPositionalParameter(self) -> Optional[Parameter]:
        items = [x for x in self.parameters if x.kind ==
                 ParameterKind.VarPositional]
        if len(items) > 0:
            return items[0]
        return None

    def getVarKeywordParameter(self) -> Optional[Parameter]:
        items = [x for x in self.parameters if x.kind ==
                 ParameterKind.VarKeyword]
        if len(items) > 0:
            return items[0]
        return None
