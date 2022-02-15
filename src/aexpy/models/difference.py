from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from .description import ApiEntry


class BreakingRank(Enum):
    Unknown = -1
    Compatible = 0
    Low = 30
    Medium = 60
    High = 100


@dataclass
class DiffEntry:
    id: "str" = ""
    kind: "str" = ""
    rank: "BreakingRank" = BreakingRank.Unknown
    message: "str" = ""
    data: "dict[str, Any]" = field(default_factory=dict)
    old: "ApiEntry | None" = field(default=None, repr=False)
    new: "ApiEntry | None" = field(default=None, repr=False)
