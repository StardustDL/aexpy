from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import Distribution, Release


class Preprocessor(Producer):
    @abstractmethod
    def preprocess(self, release: "Release") -> "Distribution":
        pass


def getDefault() -> "Preprocessor":
    from .default import Preprocessor
    return Preprocessor(mirror=True)
