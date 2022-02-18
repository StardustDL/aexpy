from pathlib import Path

from aexpy import getCacheDirectory
from ..producer import DefaultProducer, Producer, NoCachedProducer, ProducerOptions
from abc import ABC, abstractmethod
from ..models import Distribution, Product, Release


class Preprocessor(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "preprocessing"

    @abstractmethod
    def preprocess(self, release: "Release") -> "Distribution":
        """Preprocess a release and return a distribution."""

        pass


class DefaultPreprocessor(Preprocessor, DefaultProducer):
    def getCacheFile(self, release: "Release") -> "Path | None":
        return self.cache / "results" / release.project / f"{release.version}.json"

    def getProduct(self, release: "Release") -> "Distribution":
        return Distribution(release=release)

    def process(self, product: "Distribution", release: "Release"):
        pass

    def preprocess(self, release: "Release") -> "Distribution":
        return self.produce(release=release)


def getDefault() -> "Preprocessor":
    from .default import Preprocessor
    return Preprocessor(mirror=True)


class Empty(DefaultPreprocessor, NoCachedProducer):
    pass


def getEmpty() -> "Preprocessor":
    return Empty()
