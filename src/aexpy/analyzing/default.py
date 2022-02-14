from ..models import Distribution, ApiDescription
from . import Analyzer as Base


class Analyzer(Base):
    def analyze(self, dist: Distribution) -> ApiDescription:
        raise NotImplementedError()
