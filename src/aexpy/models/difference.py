from dataclasses import dataclass, field

from .description import ApiEntry


@dataclass
class DiffEntry:
    id: "str" = ""
    kind: "str" = ""
    message: "str" = ""
    old: "ApiEntry | None" = field(default=None, repr=False)
    new: "ApiEntry | None" = field(default=None, repr=False)
