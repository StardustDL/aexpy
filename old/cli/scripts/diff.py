from typing import Callable

from aexpy.analyses.models import (ApiCollection, ApiEntry, ApiManifest,
                                   AttributeEntry, ClassEntry, FunctionEntry,
                                   ModuleEntry)
from aexpy.diffs.models import DiffCollection, DiffEntry
from aexpy.logging.models import PayloadLog

diff: DiffCollection = DiffCollection()
OM: ApiManifest = diff.old
NM: ApiManifest = diff.new
entries: dict[str, DiffEntry] = {}
E: dict[str, DiffEntry] = {}
EL: list[DiffEntry] = []
read: Callable[[str | DiffEntry | ApiEntry], None] = lambda item: None
readapi: Callable[[ApiEntry], None] = lambda item: None
kind: Callable[[str], list[DiffEntry]] = lambda name: []
kinds: list[str] = []
# START

# put your codes here
