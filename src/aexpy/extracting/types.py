from abc import abstractmethod
from pathlib import Path

from aexpy.models import ApiDescription, Distribution

from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class TypeExtractor(MypyBasedIncrementalExtractor):
    def basicProduce(self, dist: "Distribution", product: "ApiDescription"):
        from aexpy.env import env
        env.services.extract("kwargs", dist, product=product)

    def processWithMypy(self, server: "PackageMypyServer", product: "ApiDescription", dist: "Distribution"):
        from .enriching import types

        product.clearCache()

        types.TypeEnricher(server, self.logger).enrich(product)

        product.clearCache()
