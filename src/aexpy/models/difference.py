from enum import IntEnum
from typing import Annotated, Any, override

from pydantic import BaseModel, Field

from .description import ApiEntryType


class BreakingRank(IntEnum):
    Unknown = -1
    Compatible = 0
    Low = 30
    Medium = 60
    High = 100


class VerifyState(IntEnum):
    Unknown = 0
    Fail = 50
    Pass = 100


class VerifyData(BaseModel):
    state: VerifyState = VerifyState.Unknown
    message: str = ""
    verifier: str = ""


class DiffEntry(BaseModel):
    id: str = ""
    kind: str = ""
    rank: BreakingRank = BreakingRank.Unknown
    verify: VerifyData = VerifyData()
    message: str = ""
    data: dict[str, Any] = {}
    old: Annotated[ApiEntryType, Field(discriminator="form")] | None = None
    new: Annotated[ApiEntryType, Field(discriminator="form")] | None = None
