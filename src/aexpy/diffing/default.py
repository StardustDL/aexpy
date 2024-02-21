from typing import override
from . import Differ


class DefaultDiffer(Differ):
    @override
    def diff(self, old, new, product):
        from .differs.default import DefaultDiffer

        DefaultDiffer(self.logger).diff(old, new, product)

        from .evaluators.default import DefaultEvaluator

        DefaultEvaluator(self.logger).diff(old, new, product)
