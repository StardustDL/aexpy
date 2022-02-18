from pathlib import Path
from ..producer import DefaultProducer, NoCachedProducer, Producer, ProducerOptions
from abc import ABC, abstractmethod
from ..models import Distribution, Product, Release


class Preprocessor(Producer):
    @abstractmethod
    def preprocess(self, release: "Release") -> "Distribution":
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


class _Empty(DefaultPreprocessor, NoCachedProducer):
    pass


def getEmpty() -> "Preprocessor":
    return _Empty()
