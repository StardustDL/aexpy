from ..models import Distribution, ApiDescription
from . import Extractor as Base


class Extractor(Base):
    def extract(self, dist: Distribution) -> ApiDescription:
        from .basic import Extractor as BasicExtractor
        return BasicExtractor().extract(dist)
