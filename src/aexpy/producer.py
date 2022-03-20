import dataclasses
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory, utils
from aexpy.env import ProducerConfig
from aexpy.models import Product


@dataclass
class ProducerOptions:
    """Options for Producer."""

    redo: "bool | None" = None
    """Redo producing."""
    nocache: "bool | None" = None
    """Caching producing."""
    onlyCache: "bool | None" = None
    """Only load from cache."""

    @property
    def cancache(self):
        return self.onlyCache or (self.redo != True and self.nocache != True)

    def replace(self, options: "ProducerOptions | None" = None, resolveNone: "bool" = False) -> "ProducerOptions":
        other = dataclasses.replace(self)
        if options is not None:
            if options.redo is not None:
                other.redo = options.redo
            if options.nocache is not None:
                other.nocache = options.nocache
            if options.onlyCache is not None:
                other.onlyCache = options.onlyCache
        other.resolve(resolveNone=resolveNone)
        return other

    @contextmanager
    def rewrite(self, options: "ProducerOptions | None" = None, resolveNone: "bool" = False) -> "ProducerOptions":
        """Provide a context with a temporary rewritten options."""

        oldRedo = self.redo
        oldNocache = self.nocache
        oldOnlyCache = self.onlyCache

        if options is not None:
            if options.redo is not None:
                self.redo = options.redo
            if options.nocache is not None:
                self.nocache = options.nocache
            if options.onlyCache is not None:
                self.onlyCache = options.onlyCache

        self.resolve(resolveNone)

        try:
            yield self
        finally:
            self.redo = oldRedo
            self.nocache = oldNocache
            self.onlyCache = oldOnlyCache

    def resolve(self, resolveNone: "bool" = False):
        if resolveNone:
            if self.onlyCache is None:
                self.onlyCache = False
            if self.nocache is None:
                self.nocache = False
            if self.redo is None:
                self.redo = False

        if self.onlyCache:
            self.redo = False
            self.nocache = False


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

        self.cache = cache or self.defaultCache() or getCacheDirectory()
        """The cache directory for the producer, resolve order: parameter, config, default, cache-dir."""

        self.options = self.defaultOptions().replace(options)
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

        with self.options.rewrite(resolveNone=True):
            cachedFile = None if self.options.nocache else self.getCacheFile(
                *args, **kwargs)
            logFile = None if self.options.nocache else self.getLogFile(
                *args, **kwargs)

            with self.getProduct(*args, **kwargs).produce(cachedFile, self.logger, logFile, self.options.redo, self.options.onlyCache) as product:
                if product.creation is None:
                    self.process(product, *args, **kwargs)
                else:
                    self.onCached(product, *args, **kwargs)

        return product


class NoCachedProducer(Producer):
    """Producer that produces a product without cache."""

    def defaultOptions(self):
        return ProducerOptions(nocache=True)


class IncrementalProducer(DefaultProducer):
    """Incremental producer that produces a product based on an existed product."""

    @abstractmethod
    def basicProduce(self, *args, **kwargs) -> "Product":
        """Produce the basic product, usually call other producer to produce (with cache)."""

        pass

    def getProduct(self, *args, **kwargs) -> "Product":
        if self.options.onlyCache:
            # Use the default product, no process, just for cache
            return super().getProduct(*args, **kwargs)
        else:
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

        assert basicProduct.success, "Basic product is failed."

        with utils.elapsedTimer() as elapsed:
            self.incrementalProcess(product, *args, **kwargs)

        duration = elapsed()

        self.logger.info(
            f"Incremental processing finished ({self.id()}), duration: {duration}.")

        if basicProduct.duration is not None:
            duration = duration + basicProduct.duration

        product.duration = duration
