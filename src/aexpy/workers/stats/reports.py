from . import ReportStatistician
from ...models import Report

S = ReportStatistician()

from .shared import duration, success

S.count(duration)
S.count(success)
