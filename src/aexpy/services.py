from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
import io
from logging import Logger
import logging
from aexpy import json
from aexpy.models import ApiDescription, ApiDifference, BatchRequest, BatchResult, Distribution, ProduceCache, ProduceCacheManager, ProduceState, Product, Release, ReleasePair, Report
from aexpy.utils import elapsedTimer, logWithStream
from .producers import Producer
from .extracting import Extractor
from .preprocessing import Preprocessor
from .diffing import Differ
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
        self.producers: "dict[str, Producer]" = {}
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
        if name in self.producers:
            return self.producers[name]
        return None

    def register(self, service: "Producer"):
        assert service.name not in self.producers
        self.producers[service.name] = service

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
                product.duration += elapsed()

            product.creation = datetime.now()

            cache.save(product, logStream.getvalue())
        else:
            try:
                yield product
            except Exception as ex:
                logger.error(
                    f"Failed to produce {product.__class__.__qualname__} after loading from cache.", exc_info=ex)
                product.state = ProduceState.Failure

    def logPreprocess(self, name: "str", release: "Release") -> "str":
        cache = self.preprocessCache.submanager(name).get(str(release))
        return cache.log()

    def logExtract(self, name: "str", release: "Release") -> "str":
        cache = self.extractCache.submanager(name).get(str(release))
        return cache.log()

    def logDiff(self, name: "str", pair: "ReleasePair") -> "str":
        cache = self.diffCache.submanager(name).get(
            f"{pair.old}&{pair.new}")
        return cache.log()

    def logReport(self, name: "str", pair: "ReleasePair") -> "str":
        cache = self.reportCache.submanager(name).get(
            f"{pair.old}&{pair.new}")
        return cache.log()

    def logBatch(self, name: "str", request: "BatchRequest") -> "str":
        cache = self.batchCache.submanager(name).submanager(
            request.pipeline).get(request.project)
        return cache.log()

    def preprocess(self, name: "str", release: "Release", mode: "ProduceMode" = ProduceMode.Access, product: "Distribution | None" = None) -> "Distribution":
        preprocessor = self.getProducer(name) or Preprocessor()
        assert isinstance(preprocessor, Preprocessor)
        cache = self.preprocessCache.get(str(release))
        product = product or Distribution(release=release)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                preprocessor.preprocess(release, product)
        return product

    def extract(self, name: "str", dist: "Distribution", mode: "ProduceMode" = ProduceMode.Access, product: "ApiDescription | None" = None) -> "ApiDescription":
        extractor = self.getProducer(name) or Extractor()
        assert isinstance(extractor, Extractor)
        cache = self.extractCache.get(str(dist.release))
        product = product or ApiDescription(distribution=dist)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                extractor.extract(dist, product)
        return product

    def diff(self, name: "str", old: "ApiDescription", new: "ApiDescription", mode: "ProduceMode" = ProduceMode.Access, product: "ApiDifference | None" = None) -> "ApiDifference":
        differ = self.getProducer(name) or Differ()
        assert isinstance(differ, Differ)
        cache = self.diffCache.get(
            f"{old.distribution.release}&{new.distribution.release}")
        product = product or ApiDifference(
            old=old.distribution, new=new.distribution)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                differ.diff(old, new, product)
        return product

    def report(self, name: "str", oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference", mode: "ProduceMode" = ProduceMode.Access, product: "Report | None" = None) -> "Report":
        reporter = self.getProducer(name) or Reporter()
        assert isinstance(reporter, Reporter)
        cache = self.reportCache.get(f"{oldRelease}&{newRelease}")
        product = product or Report(old=oldRelease, new=newRelease)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                reporter.report(oldRelease, newRelease, oldDistribution,
                                newDistribution, oldDescription, newDescription, diff, product)
        return product

    def batch(self, name: "str", request: "BatchRequest", mode: "ProduceMode" = ProduceMode.Access, product: "BatchResult | None" = None) -> "BatchResult":
        batcher = self.getProducer(name) or Batcher()
        assert isinstance(batcher, Batcher)
        cache = self.batchCache.submanager(
            request.pipeline).get(request.project)
        product = product or BatchResult(project=request.project,
                                         pipeline=request.pipeline)
        with self.produce(product, cache, mode) as product:
            if product.state == ProduceState.Pending:
                batcher.batch(request, product)
        return product
