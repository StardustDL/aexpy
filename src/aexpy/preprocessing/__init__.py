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


class _Empty(Preprocessor):
    def preprocess(self, release: "Release") -> "Distribution":
        with Distribution(release=release).produce(logger=self.logger, redo=self.redo) as dist:
            return dist


def getEmpty() -> "Preprocessor":
    return _Empty()
