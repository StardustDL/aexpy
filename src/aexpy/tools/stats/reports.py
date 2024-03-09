from ...models import Report
from . import ReportStatistician

S = ReportStatistician()

from .shared import duration, success

S.count(duration)
S.count(success)
