from abc import abstractmethod
from pathlib import Path

from aexpy.models import ApiDescription, Distribution

from . import IncrementalExtractor
from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class AttributeExtractor(MypyBasedIncrementalExtractor):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "attributes"

    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from .base import Extractor
        return Extractor(self.logger).extract(dist)

    def processWithMypy(self, server: "PackageMypyServer", product: "ApiDescription", dist: "Distribution"):
        from .enriching import attributes

        product.clearCache()

        attributes.InstanceAttributeMypyEnricher(
            server, self.logger).enrich(product)

        product.clearCache()

    def processWithFallback(self, product: "ApiDescription", dist: "Distribution"):
        from .enriching import attributes

        product.clearCache()

        attributes.InstanceAttributeAstEnricher(
            self.logger).enrich(product)

        product.clearCache()
