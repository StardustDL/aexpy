import dataclasses
from enum import IntEnum
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory, utils
from aexpy.models import ProduceCache, ProduceMode, ProduceState, Product
from aexpy import json


class Producer(ABC):
    """Producer that produces a product."""

    @classmethod
    def id(cls) -> "str":
        """Returns the id of the producer, used by ProducerConfig."""
        return f"{cls.__module__}.{cls.__qualname__}"

    @classmethod
    def name(cls) -> "str":
        """Returns the name of the producer, used by default logger, and cache manager."""
        return cls.id()

    def __init__(self, logger: "Logger | None" = None) -> None:
        self.logger = logger.getChild(
            self.name()) if logger else logging.getLogger(self.name())
        """The logger for the producer."""

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

    def produce(self, cache: "ProduceCache", mode: "ProduceMode" = ProduceMode.Access, *args, **kwargs) -> "Product":
        """Produce the product, can be used in concrete produce function."""

        with self.getProduct(*args, **kwargs).produce(cache, mode, self.logger) as product:
            if product.state == ProduceState.Pending:
                self.process(product, *args, **kwargs)
            else:
                self.onCached(product, *args, **kwargs)

        return product


class IncrementalProducer(Producer):
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
        basicProduct = self.basicProduce(*args, **kwargs)
        product.load(json.loads(basicProduct.dumps()))

        self.logger.info(
            f"Incremental processing ({self.id()}), duration: {basicProduct.duration}, creation: {basicProduct.creation}.")

        assert basicProduct.success, "Basic processing failed."

        with utils.elapsedTimer() as elapsed:
            self.incrementalProcess(product, *args, **kwargs)

        duration = elapsed()

        self.logger.info(
            f"Incremental processing finished ({self.id()}), duration: {duration}.")

        if basicProduct.duration is not None:
            duration = duration + basicProduct.duration

        product.duration = duration
        product.creation = datetime.now()
