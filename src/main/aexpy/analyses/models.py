from enum import Enum
from typing import Dict, Optional, List


class ApiManifest:
    def __init__(self, project="", version="") -> None:
        self.project = project
        self.version = version


class ApiEntry:
    def __init__(self, name="", id="") -> None:
        self.name = name
        self.id = id


class ApiCollection:
    def __init__(self, manifest: Optional[ApiManifest] = None, entries: Optional[List[ApiEntry]] = None) -> None:
        self.manifest = manifest if manifest else ApiManifest()
        self.entries: List[ApiEntry] = entries if entries else []


class CollectionEntry(ApiEntry):
    def __init__(self, name="", id="", members: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name, id)
        self.members: Dict[str, str] = members if members else {}


class ItemEntry(ApiEntry):
    def __init__(self, name="", id="", bound=False) -> None:
        super().__init__(name, id)
        self.bound = bound


class SpecialKind(Enum):
    Unknown = 0
    Empty = 1
    External = 2


class SpecialEntry(ApiEntry):
    def __init__(self, name="", id="", kind=SpecialKind.Unknown, data="") -> None:
        super().__init__(name, id)
        self.kind = kind
        self.data = data


class ModuleEntry(CollectionEntry):
    def __init__(self, name="", id="", members: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name, id, members)


class ClassEntry(CollectionEntry):
    def __init__(self, name="", id="", bases: Optional[List[str]] = None, members: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name, id, members)
        self.bases: List[str] = bases if bases else []


class FieldEntry(ItemEntry):
    def __init__(self, name="", id="", bound=False, type="") -> None:
        super().__init__(name, id, bound)
        self.type = type


class ParameterKind(Enum):
    Positional = 0
    PositionalOrKeyword = 1
    VarPositional = 2
    Keyword = 3
    VarKeyword = 4
    VarKeywordCandidate = 5


class Parameter:
    def __init__(self, kind=ParameterKind.PositionalOrKeyword, name="", type="", default="", optional=False) -> None:
        self.kind = kind
        self.name = name
        self.type = type
        self.default = default
        self.optional = optional


class FunctionEntry(ItemEntry):
    def __init__(self, name="", id="", bound=False, returnType="", parameters: Optional[List[Parameter]] = None) -> None:
        super().__init__(name, id, bound)
        self.returnType = returnType
        self.parameters: List[Parameter] = parameters if parameters else []
