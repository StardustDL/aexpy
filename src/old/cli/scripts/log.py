from datetime import datetime, timedelta
from typing import Any

from aexpy.logging.models import PayloadLog

log: PayloadLog = PayloadLog()
time: datetime = datetime.now()
duration: timedelta = timedelta()
output: str = ""
error: str = ""
extra: dict[str, Any] = {}
# START

# put your codes here
