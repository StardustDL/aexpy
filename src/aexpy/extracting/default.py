from ..models import Distribution, ApiDescription
from . import Extractor as Base


class Extractor(Base):
    def extract(self, dist: Distribution) -> ApiDescription:
        raise NotImplementedError()
