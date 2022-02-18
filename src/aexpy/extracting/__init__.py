from logging import Logger
from pathlib import Path
from ..producer import DefaultProducer, NoCachedProducer, Producer
from abc import ABC, abstractmethod
from ..models import Distribution, Release, ApiDescription


class Extractor(Producer):
    @abstractmethod
    def extract(self, dist: "Distribution") -> "ApiDescription":
        pass


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
    from .basic import Extractor as BasicExtractor
    return BasicExtractor()


class _Empty(DefaultExtractor, NoCachedProducer):
    pass


def getEmpty() -> "Extractor":
    return _Empty()
