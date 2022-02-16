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


class _Empty(Reporter):
    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        with Report(oldRelease=oldRelease, newRelease=newRelease,
                    oldDistribution=oldDistribution, newDistribution=newDistribution,
                    oldDescription=oldDescription, newDescription=newDescription,
                    diff=diff, bc=bc).produce(logger=self.logger, redo=self.redo) as report:
            return report


def getEmpty() -> "Reporter":
    return _Empty()
