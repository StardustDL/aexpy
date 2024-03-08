from typing import override

from ..models import ApiDescription
from ..models.description import FunctionEntry
from .enriching.callgraph import Callgraph
from .third.mypyserver import MypyExtractor


class KwargsExtractor(MypyExtractor):
    def enrichCallgraph(self, /, product: ApiDescription, cg: Callgraph):
        callees: dict[str, set[str]] = {}

        for caller in cg.items.values():
            cur = set()
            for site in caller.sites:
                for target in site.targets:
                    cur.add(target)
            callees[caller.id] = cur

        for key, value in callees.items():
            entry = product[key]
            if not isinstance(entry, FunctionEntry):
                continue
            entry.callees = list(value)

        product.calcCallers()

    @override
    def process(self, /, server, product, dist):
        from .enriching import kwargs

        product.clearCache()
        from .enriching.callgraph.type import TypeCallgraphBuilder

        cg = TypeCallgraphBuilder(server, self.logger).build(product)
        self.enrichCallgraph(product, cg)
        kwargs.KwargsEnricher(cg, self.logger).enrich(product)

        product.clearCache()

    @override
    def fallback(self, /, product, dist):
        from .enriching import kwargs

        product.clearCache()
        from .enriching.callgraph.basic import BasicCallgraphBuilder

        cg = BasicCallgraphBuilder(self.logger).build(product)
        self.enrichCallgraph(product, cg)
        kwargs.KwargsEnricher(Callgraph(), self.logger).enrich(product)
        product.clearCache()
