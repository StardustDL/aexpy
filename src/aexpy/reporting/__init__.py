from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import Distribution, Release, ApiDescription, ApiDifference, ApiBreaking, Report


class Reporter(Producer):
    @abstractmethod
    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        pass


def getDefault() -> "Reporter":
    from .default import Reporter
    return Reporter()
