from logging import Logger
from typing import Callable

from click import Path
from aexpy.models import Release, Distribution, ApiDescription, ApiDifference, ApiBreaking, Report
from aexpy.producer import ProducerOptions
from . import Empty, Reporter


class Collector(Empty):
    pass


class FuncCollector(Collector):
    def __init__(self, logger: "Logger | None" = None, collector: "Callable[[Release, Release,Distribution, Distribution, ApiDescription, ApiDescription, ApiDifference, ApiBreaking], None]" = None) -> None:
        super().__init__(logger, None, None)
        self.collector = collector

    def process(self, product: "Report", oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking"):
        self.collector(oldRelease, newRelease, oldDistribution,
                       newDistribution, oldDescription, newDescription, diff, bc)
