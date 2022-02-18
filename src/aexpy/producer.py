from contextlib import contextmanager
from dataclasses import dataclass
import dataclasses
import logging
from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory, utils
from aexpy.models import Product


@dataclass
class ProducerOptions:
    redo: "bool" = False
    cached: "bool" = True

    @contextmanager
    def rewrite(self, redo: "bool | None", cached: "bool | None" = None) -> "ProducerOptions":
        if redo is not None:
            oldRedo = self.redo
            self.redo = redo
        if cached is not None:
            oldCached = self.cached
            self.cached = cached

        yield self

        if redo is not None:
            self.redo = oldRedo
        if cached is not None:
            self.cached = oldCached


class Producer(ABC):
    def id(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    def stage(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}".split(".")[1]

    def defaultCache(self):
        return getCacheDirectory() / self.stage()

    def defaultOptions(self):
        return ProducerOptions()

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        self.logger = logger.getChild(
            self.id()) if logger else logging.getLogger(self.id())
        self.cache = cache or self.defaultCache()
        self.options = options or self.defaultOptions()


class NoCachedProducer(Producer):
    def defaultOptions(self):
        return ProducerOptions(cached=False)


class DefaultProducer(Producer):
    @abstractmethod
    def getCacheFile(self, *args, **kwargs) -> "Path | None":
        pass

    def getLogFile(self, *args, **kwargs) -> "Path | None":
        cacheFile = self.getCacheFile(*args, **kwargs)
        return cacheFile.with_suffix(".log") if cacheFile else None

    @abstractmethod
    def getProduct(self, *args, **kwargs) -> "Product":
        pass

    def process(self, product: "Product", *args, **kwargs):
        pass

    def produce(self, *args, **kwargs) -> "Product":
        cachedFile = self.getCacheFile(
            *args, **kwargs) if self.options.cached else None
        logFile = self.getLogFile(
            *args, **kwargs) if self.options.cached else None
        with self.getProduct(*args, **kwargs).produce(cachedFile, self.logger, logFile, self.options.redo) as product:
            if product.creation is None:
                self.process(product, *args, **kwargs)

        return product


class IncrementalProducer(DefaultProducer):
    @abstractmethod
    def basicProduce(self, *args, **kwargs) -> "Product":
        pass

    def getProduct(self, *args, **kwargs) -> "Product":
        product = self.basicProduce(*args, **kwargs)
        self._basicProduct = product
        other = dataclasses.replace(product)
        return other

    def process(self, product: "Product", *args, **kwargs):
        self.logger.info(
            f"Incremental processing, base product log file: {self._basicProduct.logFile}.")
