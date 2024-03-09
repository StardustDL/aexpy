from ...models import Distribution
from . import DistStatistician

S = DistStatistician()

from .shared import duration, success

S.count(duration)
S.count(success)


@S.count
def loc(data: Distribution):
    return data.locCount


@S.count
def filesize(data: Distribution):
    return data.fileSize


@S.count
def filecount(data: Distribution):
    return data.fileCount


@S.count
def dependencies(data: Distribution):
    return len(data.dependencies)


@S.count
def topmodules(data: Distribution):
    return len(data.topModules)


@S.count
def pyversion(data: Distribution):
    try:
        return int(data.pyversion.split(".")[1])
    except Exception:
        return 0
