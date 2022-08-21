from abc import ABC, abstractmethod
from pathlib import Path

from aexpy import getCacheDirectory

from ..models import Distribution, ProduceCache, ProduceMode, Product, Release
from ..producer import Producer


class Preprocessor(Producer):
    def getProduct(self, release: "Release") -> "Distribution":
        return Distribution(release=release)

    def process(self, product: "Distribution", mode: "ProduceMode", release: "Release"):
        pass

    def preprocess(self, release: "Release", cache: "ProduceCache", mode: "ProduceMode" = ProduceMode.Access) -> "Distribution":
        """Preprocess a release and return a distribution."""
        return self.produce(cache, mode, release=release)

    def fromcache(self, input: "Release", cache: "ProduceCache") -> "Distribution":
        return self.preprocess(input, cache, ProduceMode.Read)


def getDefault() -> "Preprocessor":
    from .pip import PipPreprocessor
    return PipPreprocessor(mirror=True)
