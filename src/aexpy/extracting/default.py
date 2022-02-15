from ..models import Distribution, ApiDescription
from . import Extractor as Base


class Extractor(Base):
    def analyze(self, dist: Distribution) -> ApiDescription:
        raise NotImplementedError()
