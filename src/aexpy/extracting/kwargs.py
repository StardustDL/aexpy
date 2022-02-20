from abc import abstractmethod
from asyncio.log import logger
from pathlib import Path
from aexpy.models import ApiDescription, Distribution
from . import IncrementalExtractor
from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class KwargsExtractor(MypyBasedIncrementalExtractor):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "kwargs"

    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from .attributes import AttributeExtractor
        return AttributeExtractor(self.logger).extract(dist)

    def processWithMypy(self, server: "PackageMypyServer", product: "ApiDescription", dist: "Distribution"):
        from .enriching import kwargs

        product.clearCache()

        from .enriching.callgraph.type import TypeCallgraphBuilder
        cg = TypeCallgraphBuilder(server, logger).build(product)
        kwargs.KwargsEnricher(cg, logger).enrich(product)

        product.clearCache()

    def processWithFallback(self, product: "ApiDescription", dist: "Distribution"):
        from .enriching import kwargs

        product.clearCache()

        from .enriching.callgraph.basic import BasicCallgraphBuilder
        cg = BasicCallgraphBuilder(logger).build(product)
        kwargs.KwargsEnricher(cg, logger).enrich(product)

        product.clearCache()
