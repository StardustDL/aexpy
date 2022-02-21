from contextlib import contextmanager
from dataclasses import dataclass
import dataclasses
from datetime import timedelta
import logging
from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory, utils
from aexpy.env import ProducerConfig
from aexpy.models import Product


@dataclass
class ProducerOptions:
    """Options for Producer."""

    redo: "bool" = False
    """Redo producing."""
    cached: "bool" = True
    """Caching producing."""
    onlyCache: "bool" = False
    """Only load from cache."""

    def replace(self, redo: "bool | None", cached: "bool | None" = None, onlyCache: "bool | None" = None) -> "ProducerOptions":
        """Generate a new options with replaced values."""

        item = dataclasses.replace(self)
        if redo is not None:
            item.redo = redo
        if cached is not None:
            item.cached = cached
        if onlyCache is not None:
            item.onlyCache = onlyCache
        item.resolve()
        return item

    @contextmanager
    def rewrite(self, redo: "bool | None", cached: "bool | None" = None, onlyCache: "bool | None" = None) -> "ProducerOptions":
        """Provide a context with a temporary rewritten options."""

        oldRedo = self.redo
        oldCached = self.cached
        oldOnlyCache = self.onlyCache

        if redo is not None:
            self.redo = redo
        if cached is not None:
            self.cached = cached
        if onlyCache is not None:
            self.onlyCache = onlyCache

        self.resolve()
        yield self

        self.redo = oldRedo
        self.cached = oldCached
        self.onlyCache = oldOnlyCache

    def resolve(self):
        self.redo = self.redo and not self.onlyCache
        self.cached = self.cached or self.onlyCache


class Producer(ABC):
    """Producer that produces a product."""

    @classmethod
    def id(cls):
        """Returns the id of the producer, used by ProducerConfig and default logger."""

        return f"{cls.__module__}.{cls.__qualname__}"

    def defaultCache(self) -> "Path | None":
        """Returns the default cache directory for the producer."""

        return None

    def defaultOptions(self) -> "ProducerOptions":
        """Returns the default options for the producer."""

        return ProducerOptions()

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        self.logger = logger.getChild(
            self.id()) if logger else logging.getLogger(self.id())
        """The logger for the producer."""

        from .env import env
        config = env.getConfig(self) or ProducerConfig()

        self.cache = cache or (getCacheDirectory().joinpath(Path(
            config.cache)) if config.cache else None) or self.defaultCache() or getCacheDirectory()
        """The cache directory for the producer, resolve order: parameter, config, default, cache-dir."""

        self.options = options or self.defaultOptions().replace(
            config.redo, config.cached, config.onlyCache)
        """The options for the producer."""


class DefaultProducer(Producer):
    """Producer that produces a product with default cache and log logic (use product.produce context)."""

    @abstractmethod
    def getCacheFile(self, *args, **kwargs) -> "Path | None":
        """Returns the cache file for the product."""

        pass

    def getLogFile(self, *args, **kwargs) -> "Path | None":
        """Returns the log file for the product."""

        cacheFile = self.getCacheFile(*args, **kwargs)
        return cacheFile.with_suffix(".log") if cacheFile else None

    @abstractmethod
    def getProduct(self, *args, **kwargs) -> "Product":
        """Generate the initial product for the producer."""

        pass

    def process(self, product: "Product", *args, **kwargs):
        """Process the product."""

        pass

    def onCached(self, product: "Product", *args, **kwargs):
        """Called when the product is cached and has been loaded from cache file."""

        pass

    def produce(self, *args, **kwargs) -> "Product":
        """Produce the product, can be used in concrete produce function."""

        cachedFile = self.getCacheFile(
            *args, **kwargs) if self.options.cached else None
        logFile = self.getLogFile(
            *args, **kwargs) if self.options.cached else None

        with self.getProduct(*args, **kwargs).produce(cachedFile, self.logger, logFile, self.options.redo, self.options.onlyCache) as product:
            if product.creation is None:
                self.process(product, *args, **kwargs)
            else:
                self.onCached(product, *args, **kwargs)

        return product


class NoCachedProducer(Producer):
    """Producer that produces a product without cache."""

    def defaultOptions(self):
        return ProducerOptions(cached=False)


class IncrementalProducer(DefaultProducer):
    """Incremental producer that produces a product based on an existed product."""

    @abstractmethod
    def basicProduce(self, *args, **kwargs) -> "Product":
        """Produce the basic product, usually call other producer to produce (with cache)."""

        pass

    def getProduct(self, *args, **kwargs) -> "Product":
        product = self.basicProduce(*args, **kwargs)
        self._basicProduct = product
        other = dataclasses.replace(product)
        return other

    def incrementalProcess(self, product: "Product", *args, **kwargs):
        """Incremental process the  product."""

        pass

    def process(self, product: "Product", *args, **kwargs):
        basicProduct = self._basicProduct
        del self._basicProduct

        self.logger.info(
            f"Incremental processing ({self.id()}), base product log file: {basicProduct.logFile}, duration: {basicProduct.duration}, creation: {basicProduct.creation}.")

        with utils.elapsedTimer() as elapsed:
            self.incrementalProcess(product, *args, **kwargs)

        duration = elapsed()

        self.logger.info(
            f"Incremental processing finished ({self.id()}), duration: {duration}.")

        if basicProduct.duration is not None:
            duration = duration + basicProduct.duration

        product.duration = duration
