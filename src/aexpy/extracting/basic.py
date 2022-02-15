from ..models import Distribution, ApiDescription
from . import Extractor as Base
from .environments import CondaEnvironment
from .. import getAppDirectory


class Extractor(Base):
    def extract(self, dist: "Distribution") -> "ApiDescription":
        with CondaEnvironment() as run:
            run(f"python -m aexpy.extracting", cwd=getAppDirectory().parent)
        return ApiDescription()
