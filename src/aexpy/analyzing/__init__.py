from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import Distribution, Release, ApiDescription


class Analyzer(Producer):
    @abstractmethod
    def analyze(self, dist: "Distribution") -> "ApiDescription":
        pass


def getDefault() -> "Analyzer":
    from .default import Analyzer
    return Analyzer()
