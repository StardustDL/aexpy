from datetime import timedelta, datetime
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PayloadLog:
    time: datetime = field(default_factory=lambda: datetime.now())
    duration: timedelta = field(default=timedelta(seconds=0))
    output: str = ""
    error: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
