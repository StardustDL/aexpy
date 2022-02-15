from logging import Logger
from pathlib import Path
from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import Distribution, Release, ApiDescription


class Extractor(Producer):
    @abstractmethod
    def extract(self, dist: "Distribution") -> "ApiDescription":
        pass


def getDefault() -> "Extractor":
    from .default import Extractor
    return Extractor()
