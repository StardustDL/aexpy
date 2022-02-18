from aexpy.models import ApiDescription, Distribution
from . import IncrementalExtractor

class AttributeExtractor(IncrementalExtractor):
    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from .basic import Extractor
        return Extractor(self.logger).extract(dist)