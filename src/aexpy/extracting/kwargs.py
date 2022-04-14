from abc import abstractmethod
from pathlib import Path
from aexpy.extracting.enriching.callgraph import Callgraph

from aexpy.models import ApiDescription, Distribution
from aexpy.models.description import FunctionEntry

from . import IncrementalExtractor
from .third.mypyserver import MypyBasedIncrementalExtractor, PackageMypyServer


class KwargsExtractor(MypyBasedIncrementalExtractor):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "kwargs"

    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from .attributes import AttributeExtractor
        return AttributeExtractor(self.logger).extract(dist)

    def enrichCallgraph(self, product: "ApiDescription", cg: "Callgraph"):
        callees: "dict[str, set[str]]" = {}

        for caller in cg.items.values():
            cur = set()
            for site in caller.sites:
                for target in site.targets:
                    cur.add(target)
            callees[caller.id] = cur

        for key, value in callees.items():
            entry = product.entries.get(key)
            if not isinstance(entry, FunctionEntry):
                continue
            entry.callees = list(value)
        
        product.calcCallers()

    def processWithMypy(self, server: "PackageMypyServer", product: "ApiDescription", dist: "Distribution"):
        from .enriching import kwargs

        product.clearCache()

        from .enriching.callgraph.type import TypeCallgraphBuilder
        cg = TypeCallgraphBuilder(server, self.logger).build(product)
        self.enrichCallgraph(product, cg)
        kwargs.KwargsEnricher(cg, self.logger).enrich(product)

        product.clearCache()

    def processWithFallback(self, product: "ApiDescription", dist: "Distribution"):
        from .enriching import kwargs

        product.clearCache()

        from .enriching.callgraph.basic import BasicCallgraphBuilder
        cg = BasicCallgraphBuilder(self.logger).build(product)
        self.enrichCallgraph(product, cg)
        kwargs.KwargsEnricher(Callgraph(), self.logger).enrich(product)

        product.clearCache()
