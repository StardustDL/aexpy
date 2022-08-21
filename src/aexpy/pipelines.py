import logging
from logging import Logger

from click import option
from aexpy import getCacheDirectory

from aexpy.batching import Batcher, ProjectResult
from aexpy.producer import ProducerOptions

from .batching import getDefault as getDefaultBatcher
from .differing import Differ
from .differing import getDefault as getDefaultDiffer
from .evaluating import Evaluator
from .evaluating import getDefault as getDefaultEvaluator
from .extracting import Extractor
from .extracting import getDefault as getDefaultExtractor
from .models import (ApiBreaking, ApiDescription, ApiDifference, Distribution, FileProduceCacheManager, ProduceMode, ProduceState,
                     Release, ReleasePair, Report)
from .preprocessing import Preprocessor
from .preprocessing import getDefault as getDefaultPreprocessor
from .reporting import Reporter
from .reporting import getDefault as getDefaultReporter
from .reporting.collectors import Collector, CollectorFunc, FuncCollector


class Pipeline:
    """Pipeline."""

    def __init__(self, name: "str" = "default", preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Reporter | None" = None, batcher: "Batcher | None" = None, logger: "Logger | None" = None) -> None:
        self.name = name
        self.preprocessor = preprocessor or getDefaultPreprocessor()
        self.extractor = extractor or getDefaultExtractor()
        self.differ = differ or getDefaultDiffer()
        self.evaluator = evaluator or getDefaultEvaluator()
        self.reporter = reporter or getDefaultReporter()
        self.batcher = batcher or getDefaultBatcher()

        self.logger = logger or logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}")

        assert isinstance(self.preprocessor, Preprocessor)
        assert isinstance(self.extractor, Extractor)
        assert isinstance(self.differ, Differ)
        assert isinstance(self.evaluator, Evaluator)
        assert isinstance(self.reporter, Reporter)
        assert isinstance(self.batcher, Batcher)

    def preprocess(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "Distribution":
        """Preprocess release."""

        preprocessor = self.preprocessor
        assert isinstance(preprocessor, Preprocessor)

        cache = FileProduceCacheManager(
            getCacheDirectory() / "preprocess" / "results" / preprocessor.name()).build(str(release))

        if mode == ProduceMode.Read:
            return preprocessor.fromcache(release, cache)
        if mode == ProduceMode.Access:
            try:
                return preprocessor.fromcache(release, cache)
            except Exception as ex:
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        self.logger.info(f"Preprocess {release}.")
        return preprocessor.preprocess(release, cache, mode)

    def extract(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDescription":
        """Extract release."""

        extractor = self.extractor
        assert isinstance(extractor, Extractor)

        cache = FileProduceCacheManager(
            getCacheDirectory() / "extract" / extractor.name()).build(str(release))

        if mode == ProduceMode.Read:
            return extractor.fromcache(release, cache)

        if mode == ProduceMode.Access:
            try:
                return extractor.fromcache(release, cache)
            except Exception as ex:
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
        return extractor.extract(dist)

    def diff(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDifference":
        """Differ old and new release."""

        differ = self.differ
        assert isinstance(differ, Differ)

        cache = FileProduceCacheManager(
            getCacheDirectory() / "diff" / differ.name()).build(f"{pair.old}&{pair.new}")

        if mode == ProduceMode.Read:
            return differ.fromcache(pair, cache)

        if mode == ProduceMode.Access:
            try:
                return differ.fromcache(pair, cache)
            except Exception as ex:
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
        return differ.diff(oldDes, newDes)

    def eval(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "ApiBreaking":
        """Evaluate old and new release."""

        evaluator = self.evaluator
        assert isinstance(evaluator, Evaluator)

        cache = FileProduceCacheManager(
            getCacheDirectory() / "eval" / evaluator.name()).build(f"{pair.old}&{pair.new}")

        if mode == ProduceMode.Read:
            return evaluator.fromcache(pair, cache)

        if mode == ProduceMode.Access:
            try:
                return evaluator.fromcache(pair, cache)
            except Exception as ex:
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        try:
            diff = self.diff(pair)
            assert diff.success, f"Failed to diff {pair.old} and {pair.new}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                diff = self.diff(pair, ProduceMode.Write)
                if not diff.success:
                    raise

        oldDesc = self.extract(pair.old)
        newDesc = self.extract(pair.new)

        self.logger.info(f"Evaluate {pair.old} and {pair.new}.")
        return evaluator.eval(diff, oldDesc, newDesc)

    def report(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "Report":
        """Report breaking changes between old and new release."""

        reporter = reporter or self.reporter
        assert isinstance(reporter, Reporter)

        cache = FileProduceCacheManager(
            getCacheDirectory() / "report" / reporter.name()).build(f"{pair.old}&{pair.new}")

        if mode == ProduceMode.Read:
            return reporter.fromcache(pair, cache)

        if mode == ProduceMode.Access:
            try:
                return reporter.fromcache(pair, cache)
            except Exception as ex:
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        try:
            diff = self.eval(pair)
            assert diff.success, f"Failed to evaluate {pair.old} and {pair.new}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                diff = self.eval(pair, ProduceMode.Write)
                if not diff.success:
                    raise

        oldDist = self.preprocess(pair.old)
        newDist = self.preprocess(pair.new)
        oldDesc = self.extract(pair.old)
        newDesc = self.extract(pair.new)
        diff = self.diff(pair)
        bc = self.eval(pair)

        self.logger.info(f"Report {pair.old} and {pair.new}.")
        return reporter.report(pair.old, pair.new, oldDist, newDist, oldDesc, newDesc, diff, bc)

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

    def collect(self, pair: "ReleasePair", collector: "CollectorFunc | Collector", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None):
        """Collect processed data."""

        if not isinstance(collector, Collector):
            collector = FuncCollector(self.logger, collector)

        self.report(pair, collector, evaluator,
                    differ, extractor, preprocessor)
