from typing import override

from ..models import Product

type StatDataType = dict[str, dict[str, float | dict[str, float]]]


class StatSummary(Product):
    dists: StatDataType = {}
    apis: StatDataType = {}
    changes: StatDataType = {}
    reports: StatDataType = {}

    @override
    def overview(self, /):
        return (
            super().overview()
            + f"""
  Dists: {len(self.dists)}
  APIs: {len(self.apis)}
  Changes: {len(self.changes)}
  Reports: {len(self.reports)}"""
        )
