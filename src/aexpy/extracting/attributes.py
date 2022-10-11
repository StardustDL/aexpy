from abc import abstractmethod
from pathlib import Path

from aexpy.models import ApiDescription, Distribution

from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class AttributeExtractor(MypyBasedIncrementalExtractor):
    def basicProduce(self, dist: "Distribution", product: "ApiDescription"):
        self.services.extract("base", dist, product=product)

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
