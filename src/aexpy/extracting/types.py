from typing import override

from .third.mypyserver import MypyExtractor


class TypeExtractor(MypyExtractor):
    @override
    def process(self, /, server, product, dist):
        from .enriching import types

        product.clearCache()
        types.TypeEnricher(server, self.logger).enrich(product)
        product.clearCache()
