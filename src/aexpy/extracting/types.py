from abc import abstractmethod
from pathlib import Path

from aexpy.models import ApiDescription, Distribution

from . import IncrementalExtractor
from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class TypeExtractor(MypyBasedIncrementalExtractor):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "types"

    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from .kwargs import KwargsExtractor
        return KwargsExtractor(self.logger).extract(dist)

    def processWithMypy(self, server: "PackageMypyServer", product: "ApiDescription", dist: "Distribution"):
        from .enriching import types

        product.clearCache()

        types.TypeEnricher(server, self.logger).enrich(product)

        product.clearCache()
