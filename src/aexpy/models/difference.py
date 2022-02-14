from dataclasses import dataclass, field
from typing import Any
from .description import ApiEntry


@dataclass
class DiffEntry:
    id: "str" = ""
    kind: "str" = ""
    message: "str" = ""
    data: "dict[str, Any]" = field(default_factory=dict)
    old: "ApiEntry | None" = field(default=None, repr=False)
    new: "ApiEntry | None" = field(default=None, repr=False)
