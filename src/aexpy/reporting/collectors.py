from logging import Logger
from typing import Callable

from click import Path

from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.producer import ProducerOptions

from . import Empty, Reporter

CollectorFunc = Callable[[Release, Release, Distribution, Distribution,
                          ApiDescription, ApiDescription, ApiDifference, ApiBreaking], None]


class Collector(Empty):
    pass


class FuncCollector(Collector):
    def __init__(self, logger: "Logger | None" = None, collector: "CollectorFunc" = None) -> None:
        super().__init__(logger, None, None)
        self.collector = collector

    def process(self, product: "Report", oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking"):
        self.collector(oldRelease, newRelease, oldDistribution,
                       newDistribution, oldDescription, newDescription, diff, bc)
