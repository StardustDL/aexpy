from abc import abstractmethod
from pathlib import Path

from aexpy.models import ApiDescription, Distribution, ProduceMode

from . import IncrementalExtractor
from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class AttributeExtractor(MypyBasedIncrementalExtractor):
    @classmethod
    def name(cls) -> str:
        return "attributes"

    def basicProduce(self, mode: "ProduceMode", dist: "Distribution") -> "ApiDescription":
        from .base import BaseExtractor
        return BaseExtractor(self.logger).extract(dist)

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
