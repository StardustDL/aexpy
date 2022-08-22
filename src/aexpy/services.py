from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
import io
from logging import Logger
import logging
from aexpy import json
from aexpy.models import ApiDescription, ApiDifference, BatchRequest, BatchResult, Distribution, ProduceCache, ProduceCacheManager, ProduceState, Product, Release, Report
from aexpy.utils import elapsedTimer, logWithStream
from .producers import Producer
from .extracting import Extractor
from .preprocessing import Preprocessor
from .differing import Differ
from .reporting import Reporter
from .batching import Batcher


class ProduceMode(IntEnum):
    Access = 0
    """Read from cache if available, otherwise produce."""
    Read = 1
    """Read from cache."""
    Write = 2
    """Redo and write to cache."""


class ServiceProvider:
    def __init__(self, cacheManager: "ProduceCacheManager") -> None:
        self.preprocessors: "dict[str, tuple[Preprocessor, ProduceCacheManager]]" = {
        }
        self.extractors: "dict[str, tuple[Extractor, ProduceCacheManager]]" = {
        }
        self.differs: "dict[str, tuple[Differ, ProduceCacheManager]]" = {}
        self.reporters: "dict[str, tuple[Reporter, ProduceCacheManager]]" = {}
        self.batchers: "dict[str, tuple[Batcher, ProduceCacheManager]]" = {}
        self.cacheManager: "ProduceCacheManager" = cacheManager
        self.preprocessCache: "ProduceCacheManager" = self.cacheManager.submanager(
            "preprocess")
        self.extractCache: "ProduceCacheManager" = self.cacheManager.submanager(
            "extract")
        self.diffCache: "ProduceCacheManager" = self.cacheManager.submanager(
            "diff")
        self.reportCache: "ProduceCacheManager" = self.cacheManager.submanager(
            "report")
        self.batchCache: "ProduceCacheManager" = self.cacheManager.submanager(
            "batch")

    def getProducer(self, name: "str") -> "Producer | None":
        if name in self.preprocessors:
            return self.preprocessors[name][0]
        if name in self.extractors:
            return self.extractors[name][0]
        if name in self.differs:
            return self.differs[name][0]
        if name in self.reporters:
            return self.reporters[name][0]
        if name in self.batchers:
            return self.batchers[name][0]
        return None

    def getPreprocessor(self, name: "str") -> "Preprocessor | None":
        if name in self.preprocessors:
            return self.preprocessors[name][0]
        return None

    def getExtractor(self, name: "str") -> "Extractor | None":
        if name in self.extractors:
            return self.extractors[name][0]
        return None

    def getDiffer(self, name: "str") -> "Differ | None":
        if name in self.differs:
            return self.differs[name][0]
        return None

    def getReporter(self, name: "str") -> "Reporter | None":
        if name in self.reporters:
            return self.reporters[name][0]
        return None

    def getBatcher(self, name: "str") -> "Batcher | None":
        if name in self.batchers:
            return self.batchers[name][0]
        return None

    def register(self, service: "Producer"):
        if isinstance(service, Preprocessor):
            self.preprocessors[service.name] = service, self.preprocessCache.submanager(
                service.name)
        if isinstance(service, Extractor):
            self.extractors[service.name] = service, self.extractCache.submanager(
                service.name)
        if isinstance(service, Differ):
            self.differs[service.name] = service, self.diffCache.submanager(
                service.name)
        if isinstance(service, Reporter):
            self.reporters[service.name] = service, self.reportCache.submanager(
                service.name)
        if isinstance(service, Batcher):
            self.batchers[service.name] = service, self.batchCache.submanager(
                service.name)

    @contextmanager
    def produce(self, product: "Product", cache: "ProduceCache", mode: "ProduceMode" = ProduceMode.Access, logger: "Logger | None" = None):
        """
        Provide a context to produce product.

        It will automatically use cached file, measure duration, and log to logFile if provided.

        If field duration, creation is None, it will also set them.
        """

        logger = logger or logging.getLogger(product.__class__.__qualname__)

        needProcess = mode == ProduceMode.Write

        if not needProcess:
            try:
                product.safeload(json.loads(cache.data()))
            except Exception as ex:
                logger.error(
                    f"Failed to produce {product.__class__.__qualname__} by loading cache, will reproduce", exc_info=ex)
                needProcess = True

        if needProcess:
            if mode == ProduceMode.Read:
                raise Exception(
                    f"{product.__class__.__qualname__} is not cached, cannot produce.")

            product.state = ProduceState.Pending
            product.duration = None
            product.creation = None

            logStream = io.StringIO()

            with logWithStream(logger, logStream):
                with elapsedTimer() as elapsed:
                    logger.info(f"Producing {product.__class__.__qualname__}.")
                    try:
                        yield product

                        product.state = ProduceState.Success
                        logger.info(
                            f"Produced {product.__class__.__qualname__}.")
                    except Exception as ex:
                        logger.error(
                            f"Failed to produce {product.__class__.__qualname__}.", exc_info=ex)
                        product.state = ProduceState.Failure
                if product.duration is None:
                    product.duration = elapsed()

            if product.creation is None:
                product.creation = datetime.now()

            cache.save(product, logStream.getvalue())
        else:
            try:
                yield product
            except Exception as ex:
                logger.error(
                    f"Failed to produce {product.__class__.__qualname__} after loading from cache.", exc_info=ex)
                product.state = ProduceState.Failure

    def preprocess(self, name: "str", release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "Distribution":
        preprocessor, cacheManager = self.preprocessors[name]
        cache = cacheManager.get(str(release))
        product = Distribution(release=release)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                preprocessor.preprocess(release, product)
        return product

    def extract(self, name: "str", dist: "Distribution", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDescription":
        extractor, cacheManager = self.extractors[name]
        cache = cacheManager.get(str(dist.release))
        product = ApiDescription(distribution=dist)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                extractor.extract(dist, product)
        return product

    def diff(self, name: "str", old: "ApiDescription", new: "ApiDescription", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDifference":
        differ, cacheManager = self.differs[name]
        cache = cacheManager.get(
            f"{old.distribution.release}&{new.distribution.release}")
        product = ApiDifference(old=old.distribution, new=new.distribution)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                differ.diff(old, new, product)
        return product

    def report(self, name: "str", oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference", mode: "ProduceMode" = ProduceMode.Access) -> "Report":
        reporter, cacheManager = self.reporters[name]
        cache = cacheManager.get(f"{oldRelease}&{newRelease}")
        product = Report(old=oldRelease, new=newRelease)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                reporter.report(oldRelease, newRelease, oldDistribution,
                                newDistribution, oldDescription, newDescription, diff, product)
        return product

    def batch(self, name: "str", request: "BatchRequest", mode: "ProduceMode" = ProduceMode.Access) -> "BatchResult":
        batcher, cacheManager = self.batchers[name]
        cache = cacheManager.submanager(request.pipeline).get(request.project)
        product = BatchResult(project=request.project,
                              pipeline=request.pipeline)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                batcher.batch(request, product)
        return product
