from abc import abstractmethod
from asyncio.log import logger
from pathlib import Path
from aexpy.models import ApiDescription, Distribution
from . import IncrementalExtractor
from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class TypeExtractor(MypyBasedIncrementalExtractor):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "types"

    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from .basic import Extractor
        return Extractor(self.logger).extract(dist)

    def processWithMypy(self, server: "PackageMypyServer", product: "ApiDescription", dist: "Distribution"):
        from .enriching import types

        product.clearCache()
        
        types.TypeEnricher(server, logger).enrich(product)

        product.clearCache()
