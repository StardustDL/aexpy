from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import Distribution, Release, ApiDescription


class Extractor(Producer):
    @abstractmethod
    def analyze(self, dist: "Distribution") -> "ApiDescription":
        pass


def getDefault() -> "Extractor":
    from .default import Extractor
    return Extractor()