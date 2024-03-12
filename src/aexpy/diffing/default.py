from typing import override

from ..producers import produce
from . import Differ


class DefaultDiffer(Differ):
    @override
    def diff(self, /, old, new, product):
        with produce(product, self.logger, raising=True) as context:
            from .differs.default import DefaultDiffer

            with context.using(DefaultDiffer()) as producer:
                producer.diff(old, new, product)

            from .evaluators.default import DefaultEvaluator

            with context.using(DefaultEvaluator()) as producer:
                producer.diff(old, new, product)

            self.name = context.combinedProducers(self)
