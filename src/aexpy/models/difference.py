from enum import IntEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field

from .description import ApiEntryType


class BreakingRank(IntEnum):
    Unknown = -1
    Compatible = 0
    Low = 30
    Medium = 60
    High = 100


class DiffEntry(BaseModel):
    id: str = ""
    kind: str = ""
    rank: BreakingRank = BreakingRank.Unknown
    message: str = ""
    data: dict[str, Any] = {}
    old: Annotated[ApiEntryType, Field(discriminator="form")] | None = None
    new: Annotated[ApiEntryType, Field(discriminator="form")] | None = None
