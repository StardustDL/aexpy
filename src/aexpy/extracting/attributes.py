from typing import override

from .third.mypyserver import MypyExtractor


class AttributeExtractor(MypyExtractor):
    @override
    def process(self, /, server, product, dist):
        from .enriching import attributes

        product.clearCache()
        attributes.InstanceAttributeMypyEnricher(server, self.logger).enrich(product)
        product.clearCache()

    @override
    def fallback(self, /, product, dist):
        from .enriching import attributes

        product.clearCache()
        attributes.InstanceAttributeAstEnricher(self.logger).enrich(product)
        product.clearCache()
