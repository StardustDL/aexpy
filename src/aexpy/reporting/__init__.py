from abc import ABC, abstractmethod
from pathlib import Path

from aexpy import getCacheDirectory

from ..models import (ApiBreaking, ApiDescription, ApiDifference, Distribution,
                      Product, Release, Report)
from ..producer import (DefaultProducer, NoCachedProducer, Producer,
                        ProducerOptions)


class Reporter(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "reporting"

    @abstractmethod
    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        """Report the differences between two versions of the API."""

        pass

    def fromcache(self, old: "Release", new: "Release") -> "Report":
        olddist, newdist = Distribution(release=old), Distribution(release=new)
        with self.options.rewrite(ProducerOptions(onlyCache=True)):
            return self.report(oldRelease=old, newRelease=new,
                               oldDistribution=olddist, newDistribution=newdist,
                               oldDescription=ApiDescription(distribution=olddist), newDescription=ApiDescription(distribution=newdist),
                               diff=ApiDifference(old=olddist, new=newdist),
                               bc=ApiBreaking(old=olddist, new=newdist))


class DefaultReporter(Reporter, DefaultProducer):
    def getCacheFile(self, oldRelease: "Release", newRelease: "Release",
                     oldDistribution: "Distribution", newDistribution: "Distribution",
                     oldDescription: "ApiDescription", newDescription: "ApiDescription",
                     diff: "ApiDifference",
                     bc: "ApiBreaking") -> "Path | None":
        return self.cache / "results" / oldRelease.project / \
            f"{oldRelease}&{newRelease}.json"

    def getOutFile(self, oldRelease: "Release", newRelease: "Release",
                   oldDistribution: "Distribution", newDistribution: "Distribution",
                   oldDescription: "ApiDescription", newDescription: "ApiDescription",
                   diff: "ApiDifference",
                   bc: "ApiBreaking") -> "Path | None":
        """Return the path to the report output file."""
        return self.cache / "reports" / oldRelease.project / \
            f"{oldRelease}&{newRelease}.txt"

    def getProduct(self, oldRelease: "Release", newRelease: "Release",
                   oldDistribution: "Distribution", newDistribution: "Distribution",
                   oldDescription: "ApiDescription", newDescription: "ApiDescription",
                   diff: "ApiDifference",
                   bc: "ApiBreaking") -> "Report":
        file = None if self.options.nocache else self.getOutFile(oldRelease=oldRelease, newRelease=newRelease, oldDistribution=oldDistribution,
                                                                 newDistribution=newDistribution, oldDescription=oldDescription, newDescription=newDescription, diff=diff, bc=bc)
        ret = Report(old=oldRelease, new=newRelease)
        ret.file = file
        return ret

    def process(self, product: "Report", oldRelease: "Release", newRelease: "Release",
                oldDistribution: "Distribution", newDistribution: "Distribution",
                oldDescription: "ApiDescription", newDescription: "ApiDescription",
                diff: "ApiDifference",
                bc: "ApiBreaking"):
        pass

    def onCached(self, product: "Report", oldRelease: "Release", newRelease: "Release",
                 oldDistribution: "Distribution", newDistribution: "Distribution",
                 oldDescription: "ApiDescription", newDescription: "ApiDescription",
                 diff: "ApiDifference",
                 bc: "ApiBreaking"):
        pass

    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        assert oldDistribution.release == oldRelease, f"{oldDistribution.release} != {oldRelease}"
        assert newDistribution.release == newRelease, f"{newDistribution.release} != {newRelease}"
        assert oldDescription.distribution.release == oldRelease, f"{oldDescription.distribution.release} != {oldRelease}"
        assert newDescription.distribution.release == newRelease, f"{newDescription.distribution.release} != {newRelease}"
        assert diff.old.release == oldRelease, f"{diff.old.release} != {oldRelease}"
        assert diff.new.release == newRelease, f"{diff.new.release} != {newRelease}"
        assert bc.old.release == oldRelease, f"{bc.old.release} != {oldRelease}"
        assert bc.new.release == newRelease, f"{bc.new.release} != {newRelease}"
        return self.produce(oldRelease=oldRelease, newRelease=newRelease, oldDistribution=oldDistribution, newDistribution=newDistribution, oldDescription=oldDescription, newDescription=newDescription, diff=diff, bc=bc)


def getDefault() -> "Reporter":
    from .generators import GeneratorReporter

    return GeneratorReporter()


class Empty(DefaultReporter, NoCachedProducer):
    def produce(self, *args, **kwargs) -> "Product":
        self.options.onlyCache = False
        self.options.nocache = True
        return super().produce(*args, **kwargs)


def getEmpty() -> "Reporter":
    return Empty()
