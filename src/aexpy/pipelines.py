import logging
from logging import Logger

from click import option
from aexpy import getCacheDirectory

from aexpy.batching import Batcher, ProjectResult
from aexpy.producers import ProducerOptions
from aexpy.services import ProduceMode

from .batching import getDefault as getDefaultBatcher
from .differing import Differ
from .differing import getDefault as getDefaultDiffer
from .extracting import Extractor
from .extracting import getDefault as getDefaultExtractor
from .models import (ApiDescription, ApiDifference, Distribution, FileProduceCacheManager, ProduceState,
                     Release, ReleasePair, Report)
from .preprocessing import Preprocessor
from .preprocessing import getDefault as getDefaultPreprocessor
from .reporting import Reporter
from .reporting import getDefault as getDefaultReporter
from .reporting.collectors import Collector, CollectorFunc, FuncCollector


class Pipeline:
    """Pipeline."""

    def __init__(self, name: "str" = "default", preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, reporter: "Reporter | None" = None, batcher: "Batcher | None" = None, logger: "Logger | None" = None) -> None:
        self.name = name
        self.preprocessor = preprocessor or getDefaultPreprocessor()
        self.extractor = extractor or getDefaultExtractor()
        self.differ = differ or getDefaultDiffer()
        self.reporter = reporter or getDefaultReporter()
        self.batcher = batcher or getDefaultBatcher()

        self.logger = logger or logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}")

        assert isinstance(self.preprocessor, Preprocessor)
        assert isinstance(self.extractor, Extractor)
        assert isinstance(self.differ, Differ)
        assert isinstance(self.reporter, Reporter)
        assert isinstance(self.batcher, Batcher)

    def preprocess(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "Distribution":
        """Preprocess release."""

        from .env import env
        services = env.services

        try:
            return services.preprocess(self.preprocessor.name, release, ProduceMode.Read)
        except Exception as ex:
            self.logger.warning(
                f"Failed to load from cache.", exc_info=ex)
            if mode == ProduceMode.Read:
                raise

        self.logger.info(f"Preprocess {release}.")
        return services.preprocess(self.preprocessor.name, release, mode)

    def extract(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDescription":
        """Extract release."""

        from .env import env
        services = env.services

        try:
            return services.extract(self.extractor.name, Distribution(release=release), ProduceMode.Read)
        except Exception as ex:
            if mode == ProduceMode.Read:
                raise
            self.logger.warning(
                f"Failed to load from cache.", exc_info=ex)

        try:
            dist = self.preprocess(release)
            assert dist.success, f"Failed to preprocess {release}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                dist = self.preprocess(release, ProduceMode.Write)
                if not dist.success:
                    raise

        self.logger.info(f"Extract {release}.")
        return services.extract(self.extractor.name, dist, mode)

    def diff(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDifference":
        """Differ old and new release."""

        from .env import env
        services = env.services

        try:
            return services.diff(self.differ.name, ApiDescription(dist=Distribution(release=pair.old)), ApiDescription(dist=Distribution(release=pair.new)), ProduceMode.Read)
        except Exception as ex:
            if mode == ProduceMode.Read:
                raise
            self.logger.warning(
                f"Failed to load from cache.", exc_info=ex)

        try:
            oldDes = self.extract(pair.old)
            assert oldDes.success, f"Failed to extract {pair.old}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                oldDes = self.extract(pair.old, ProduceMode.Write)
                if not oldDes.success:
                    raise

        try:
            newDes = self.extract(pair.new)
            assert newDes.success, f"Failed to extract {pair.new}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                newDes = self.extract(pair.new, ProduceMode.Write)
                if not newDes.success:
                    raise

        self.logger.info(f"Diff {pair.old} and {pair.new}.")
        return services.diff(self.differ.name, oldDes, newDes, mode)

    def report(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "Report":
        """Report breaking changes between old and new release."""

        from .env import env
        services = env.services

        try:
            distOld = Distribution(release=pair.old)
            distNew = Distribution(release=pair.new)
            return services.report(self.reporter.name,
                                   pair.old, pair.new,
                                   distOld, distNew,
                                   ApiDescription(dist=distOld),
                                   ApiDescription(dist=distNew),
                                   ApiDifference(old=distOld, new=distNew),
                                   ProduceMode.Read)
        except Exception as ex:
            if mode == ProduceMode.Read:
                raise
            self.logger.warning(
                f"Failed to load from cache.", exc_info=ex)

        try:
            diff = self.diff(pair)
            assert diff.success, f"Failed to evaluate {pair.old} and {pair.new}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                diff = self.diff(pair, ProduceMode.Write)
                if not diff.success:
                    raise

        oldDist = self.preprocess(pair.old)
        newDist = self.preprocess(pair.new)
        oldDesc = self.extract(pair.old)
        newDesc = self.extract(pair.new)
        diff = self.diff(pair)

        self.logger.info(f"Report {pair.old} and {pair.new}.")
        return services.report(self.reporter.name, pair.old, pair.new, oldDist, newDist, oldDesc, newDesc, diff, mode)

    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 3, batcher: "Batcher | None" = None, mode: "ProduceMode" = ProduceMode.Access) -> "ProjectResult":
        """Batch process releases."""

        # TODO: redesign batch

        batcher = batcher or self.batcher
        assert isinstance(batcher, Batcher)

        cache = FileProduceCacheManager(
            getCacheDirectory() / "batch" / batcher.name() / self.name).build(project)

        if mode == ProduceMode.Read:
            return batcher.fromcache(self.name, project, cache)

        if mode == ProduceMode.Access:
            try:
                return batcher.fromcache(self.name, project, cache)
            except Exception as ex:
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        self.logger.info(f"Batch process {project} releases.")
        return batcher.batch(self.name, project, workers, retry)

    def index(self, project: "str", workers: "int | None" = None, retry: "int" = 3, mode: "ProduceMode" = ProduceMode.Access) -> "ProjectResult":
        from aexpy.batching.loaders import BatchLoader
        loader = BatchLoader(provider=self.name)
        return self.batch(project, batcher=loader, workers=workers, retry=retry, mode=mode)

    def collect(self, pair: "ReleasePair", collector: "CollectorFunc | Collector", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None):
        """Collect processed data."""

        if not isinstance(collector, Collector):
            collector = FuncCollector(self.logger, collector)

        self.report(pair, collector, evaluator,
                    differ, extractor, preprocessor)
