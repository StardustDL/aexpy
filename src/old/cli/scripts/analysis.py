from typing import Callable

from aexpy.analyses.models import (ApiCollection, ApiEntry, ApiManifest,
                                   AttributeEntry, ClassEntry, FunctionEntry,
                                   ModuleEntry)
from aexpy.logging.models import PayloadLog

api: ApiCollection = ApiCollection
A: ApiCollection = api
manifest: ApiManifest = api.manifest
entries: dict[str, ApiEntry] = {}
E: dict[str, ApiEntry] = {}
EL: list[ApiEntry] = []
names: dict[str, list[ApiEntry]] = {}
N: dict[str, list[ApiEntry]] = {}
M: dict[str, ModuleEntry] = {}
C: dict[str, ClassEntry] = {}
F: dict[str, FunctionEntry] = {}
P: dict[str, AttributeEntry] = {}
ML: list[ModuleEntry] = []
CL: list[ClassEntry] = []
FL: list[FunctionEntry] = []
PL: list[AttributeEntry] = []
log: PayloadLog = PayloadLog()
read: Callable[[str | ApiEntry], None] = lambda item: None
# START

# put your codes here
