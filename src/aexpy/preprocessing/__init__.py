from abc import ABC, abstractmethod
from pathlib import Path

from aexpy import getCacheDirectory

from ..models import Distribution, Product, Release
from ..producer import (DefaultProducer, NoCachedProducer, Producer,
                        ProducerOptions)


class Preprocessor(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "preprocessing"

    @abstractmethod
    def preprocess(self, release: "Release") -> "Distribution":
        """Preprocess a release and return a distribution."""

        pass

    def fromcache(self, input: "Release") -> "Distribution":
        with self.options.rewrite(ProducerOptions(onlyCache=True)):
            return self.preprocess(input)


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
    from .pip import PipPreprocessor
    return PipPreprocessor(mirror=True)


class Empty(DefaultPreprocessor, NoCachedProducer):
    def produce(self, *args, **kwargs) -> "Product":
        self.options.onlyCache = False
        self.options.nocache = True
        return super().produce(*args, **kwargs)


def getEmpty() -> "Preprocessor":
    return Empty()
