from contextlib import contextmanager
from dataclasses import dataclass
import dataclasses
import logging
from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory, utils
from aexpy.env import ProducerConfig
from aexpy.models import Product


@dataclass
class ProducerOptions:
    redo: "bool" = False
    cached: "bool" = True

    def replace(self, redo: "bool | None", cached: "bool | None" = None) -> "ProducerOptions":
        item = dataclasses.replace(self)
        if redo is not None:
            item.redo = redo
        if cached is not None:
            item.cached = cached
        return item

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
    @classmethod
    def id(cls):
        return f"{cls.__module__}.{cls.__qualname__}"

    def defaultCache(self) -> "Path | None":
        return None

    def defaultOptions(self) -> "ProducerOptions":
        return ProducerOptions()

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        self.logger = logger.getChild(
            self.id()) if logger else logging.getLogger(self.id())

        from .env import env

        config = env.getConfig(self) or ProducerConfig()
        self.cache = cache or (Path(
            config.cache) if config.cache else None) or self.defaultCache() or getCacheDirectory()
        self.options = options or self.defaultOptions().replace(config.redo, config.cached)


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

    def onCached(self, product: "Product", *args, **kwargs):
        pass

    def produce(self, *args, **kwargs) -> "Product":
        cachedFile = self.getCacheFile(
            *args, **kwargs) if self.options.cached else None
        logFile = self.getLogFile(
            *args, **kwargs) if self.options.cached else None

        with self.getProduct(*args, **kwargs).produce(cachedFile, self.logger, logFile, self.options.redo) as product:
            if product.creation is None:
                self.process(product, *args, **kwargs)
            else:
                self.onCached(product, *args, **kwargs)

        return product


class NoCachedProducer(Producer):
    def defaultOptions(self):
        return ProducerOptions(cached=False)


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
