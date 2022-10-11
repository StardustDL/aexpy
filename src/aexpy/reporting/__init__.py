from abc import ABC, abstractmethod
from pathlib import Path

from ..models import (ApiDescription, ApiDifference, Distribution,
                      Product, Release, Report)
from ..producers import (Producer,
                         ProducerOptions)


class Reporter(Producer):
    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference", product: "Report"):
        """Report the differences between two versions of the API."""
        assert oldDistribution.release == oldRelease, f"{oldDistribution.release} != {oldRelease}"
        assert newDistribution.release == newRelease, f"{newDistribution.release} != {newRelease}"
        assert oldDescription.distribution and newDescription.distribution
        assert oldDescription.distribution.release == oldRelease, f"{oldDescription.distribution.release} != {oldRelease}"
        assert newDescription.distribution.release == newRelease, f"{newDescription.distribution.release} != {newRelease}"
        assert diff.old and diff.new
        assert diff.old.release == oldRelease, f"{diff.old.release} != {oldRelease}"
        assert diff.new.release == newRelease, f"{diff.new.release} != {newRelease}"
