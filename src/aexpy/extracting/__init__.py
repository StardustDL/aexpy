from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory

from ..models import ApiDescription, Distribution, Product, Release
from ..producer import (DefaultProducer, IncrementalProducer, NoCachedProducer,
                        Producer, ProducerOptions)


class Extractor(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "extracting"

    @abstractmethod
    def extract(self, dist: "Distribution") -> "ApiDescription":
        """Extract an API description from a distribution."""

        pass

    def fromcache(self, input: "Release") -> "ApiDescription":
        with self.options.rewrite(ProducerOptions(onlyCache=True)):
            return self.extract(Distribution(release=input))


class DefaultExtractor(Extractor, DefaultProducer):
    def getCacheFile(self, dist: "Distribution") -> "Path | None":
        return self.cache / dist.release.project / f"{dist.release.version}.json"

    def getProduct(self, dist: "Distribution") -> "ApiDescription":
        return ApiDescription(distribution=dist)

    def process(self, product: "ApiDescription", dist: "Distribution"):
        pass

    def extract(self, dist: "Distribution") -> "ApiDescription":
        return self.produce(dist=dist)


def getDefault() -> "Extractor":
    # from .basic import Extractor as BasicExtractor
    from .types import TypeExtractor
    return TypeExtractor()


class Empty(DefaultExtractor, NoCachedProducer):
    def produce(self, *args, **kwargs) -> "Product":
        self.options.onlyCache = False
        self.options.nocache = True
        return super().produce(*args, **kwargs)


def getEmpty() -> "Extractor":
    return Empty()


class IncrementalExtractor(IncrementalProducer, DefaultExtractor):
    @abstractmethod
    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        pass

    def incrementalProcess(self, product: "ApiDescription", dist: "Distribution"):
        pass
