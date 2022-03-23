import logging
from logging import Logger

from click import option

from aexpy.batching import Batcher, ProjectResult
from aexpy.producer import ProducerOptions

from .batching import getDefault as getDefaultBatcher
from .differing import Differ
from .differing import getDefault as getDefaultDiffer
from .differing import getEmpty as getEmptyDiffer
from .evaluating import Evaluator
from .evaluating import getDefault as getDefaultEvaluator
from .evaluating import getEmpty as getEmptyEvaluator
from .extracting import Extractor
from .extracting import getDefault as getDefaultExtractor
from .extracting import getEmpty as getEmptyExtractor
from .models import (ApiBreaking, ApiDescription, ApiDifference, Distribution,
                     Release, ReleasePair, Report)
from .preprocessing import Preprocessor
from .preprocessing import getDefault as getDefaultPreprocessor
from .preprocessing import getEmpty as getEmptyPreprocessor
from .reporting import Reporter
from .reporting import getDefault as getDefaultReporter
from .reporting import getEmpty as getEmptyReporter
from .reporting.collectors import Collector, CollectorFunc, FuncCollector


class Pipeline:
    """Pipeline."""

    def __init__(self, name: "str" = "default", preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Reporter | None" = None, batcher: "Batcher | None" = None, options: "ProducerOptions | None" = None, logger: "Logger | None" = None) -> None:
        self.name = name
        self.preprocessor = preprocessor or getDefaultPreprocessor()
        self.extractor = extractor or getDefaultExtractor()
        self.differ = differ or getDefaultDiffer()
        self.evaluator = evaluator or getDefaultEvaluator()
        self.reporter = reporter or getDefaultReporter()
        self.batcher = batcher or getDefaultBatcher()

        self.options = options or ProducerOptions()

        self.logger = logger or logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}")

        assert isinstance(self.preprocessor, Preprocessor)
        assert isinstance(self.extractor, Extractor)
        assert isinstance(self.differ, Differ)
        assert isinstance(self.evaluator, Evaluator)
        assert isinstance(self.reporter, Reporter)
        assert isinstance(self.batcher, Batcher)
        assert isinstance(self.options, ProducerOptions)

    def preprocess(self, release: "Release", preprocessor: "Preprocessor | None" = None, options: "ProducerOptions | None" = None) -> "Distribution":
        """Preprocess release."""

        preprocessor = preprocessor or self.preprocessor
        assert isinstance(preprocessor, Preprocessor)

        with self.options.rewrite(options):
            with preprocessor.options.rewrite(self.options):
                if preprocessor.options.cancache:
                    try:
                        return preprocessor.fromcache(release)
                    except Exception as ex:
                        self.logger.warning(
                            f"Failed to load from cache.", exc_info=ex)

                self.logger.info(f"Preprocess {release}.")
                return preprocessor.preprocess(release)

    def extract(self, release: "Release", extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, options: "ProducerOptions | None" = None) -> "ApiDescription":
        """Extract release."""

        extractor = extractor or self.extractor
        assert isinstance(extractor, Extractor)

        with self.options.rewrite(options):
            with extractor.options.rewrite(self.options):
                if extractor.options.cancache:
                    try:
                        return extractor.fromcache(release)
                    except Exception as ex:
                        self.logger.warning(
                            f"Failed to load from cache.", exc_info=ex)

                try:
                    dist = self.preprocess(release, preprocessor, options=ProducerOptions(
                        onlyCache=self.options.onlyCache))
                    assert dist.success, f"Failed to preprocess {release}"
                except:
                    if self.options.onlyCache or not self.options.redo:
                        raise
                    else:
                        dist = self.preprocess(
                            release, preprocessor, options=ProducerOptions(redo=True))
                        if not dist.success:
                            raise

                self.logger.info(f"Extract {release}.")
                return extractor.extract(dist)

    def diff(self, pair: "ReleasePair", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, options: "ProducerOptions | None" = None) -> "ApiDifference":
        """Differ old and new release."""

        differ = differ or self.differ
        assert isinstance(differ, Differ)

        with self.options.rewrite(options):
            with differ.options.rewrite(self.options):
                old, new = pair.old, pair.new
                if differ.options.cancache:
                    try:
                        return differ.fromcache(old, new)
                    except Exception as ex:
                        self.logger.warning(
                            f"Failed to load from cache.", exc_info=ex)

                try:
                    oldDes = self.extract(
                        old, extractor, preprocessor, options=ProducerOptions(onlyCache=self.options.onlyCache))
                    assert oldDes.success, f"Failed to extract {old}"
                except:
                    if self.options.onlyCache or not self.options.redo:
                        raise
                    else:
                        oldDes = self.extract(
                            old, extractor, preprocessor, options=ProducerOptions(redo=True))
                        if not oldDes.success:
                            raise

                try:
                    newDes = self.extract(
                        new, extractor, preprocessor, options=ProducerOptions(onlyCache=self.options.onlyCache))
                    assert newDes.success, f"Failed to extract {new}"
                except:
                    if self.options.onlyCache or not self.options.redo:
                        raise
                    else:
                        newDes = self.extract(
                            new, extractor, preprocessor, options=ProducerOptions(redo=True))
                        if not newDes.success:
                            raise

                self.logger.info(f"Differ {old} and {new}.")

                return differ.diff(oldDes, newDes)

    def eval(self, pair: "ReleasePair", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, options: "ProducerOptions | None" = None) -> "ApiBreaking":
        """Evaluate old and new release."""

        evaluator = evaluator or self.evaluator
        assert isinstance(evaluator, Evaluator)

        with self.options.rewrite(options):
            with evaluator.options.rewrite(self.options):
                old, new = pair.old, pair.new
                if evaluator.options.cancache:
                    try:
                        return evaluator.fromcache(old, new)
                    except Exception as ex:
                        self.logger.warning(
                            f"Failed to load from cache.", exc_info=ex)

                onlyCachedOptions = ProducerOptions(
                    onlyCache=self.options.onlyCache)

                try:
                    diff = self.diff(pair, differ, extractor,
                                     preprocessor, options=onlyCachedOptions)
                    assert diff.success, f"Failed to diff {old} and {new}"
                except:
                    if self.options.onlyCache or not self.options.redo:
                        raise
                    else:
                        diff = self.diff(pair, differ, extractor,
                                         preprocessor, options=ProducerOptions(redo=True))
                        if not diff.success:
                            raise

                oldDesc = self.extract(
                    old, extractor, preprocessor, onlyCachedOptions)
                newDesc = self.extract(
                    new, extractor, preprocessor, onlyCachedOptions)

                self.logger.info(f"Evaluate {old} and {new}.")
                return evaluator.eval(diff, oldDesc, newDesc)

    def report(self, pair: "ReleasePair", reporter: "Reporter | None" = None, evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, options: "ProducerOptions | None" = None) -> "Report":
        """Report breaking changes between old and new release."""

        reporter = reporter or self.reporter
        assert isinstance(reporter, Reporter)

        with self.options.rewrite(options):
            with reporter.options.rewrite(self.options):
                old, new = pair.old, pair.new
                if reporter.options.cancache:
                    try:
                        return reporter.fromcache(old, new)
                    except Exception as ex:
                        self.logger.warning(
                            f"Failed to load from cache.", exc_info=ex)

                onlyCachedOptions = ProducerOptions(
                    onlyCache=self.options.onlyCache)

                try:
                    bc = self.eval(pair, evaluator, differ,
                                   extractor, preprocessor, onlyCachedOptions)
                    assert bc.success, f"Failed to evaluate {old} and {new}"
                except:
                    if self.options.onlyCache or not self.options.redo:
                        raise
                    else:
                        bc = self.eval(pair, evaluator, differ,
                                       extractor, preprocessor, options=ProducerOptions(redo=True))
                        if not bc.success:
                            raise

                oldDist = self.preprocess(old, preprocessor, onlyCachedOptions)
                newDist = self.preprocess(new, preprocessor, onlyCachedOptions)
                oldDesc = self.extract(
                    old, extractor, preprocessor, onlyCachedOptions)
                newDesc = self.extract(
                    new, extractor, preprocessor, onlyCachedOptions)
                diff = self.diff(pair, differ, extractor,
                                 preprocessor, onlyCachedOptions)
                bc = self.eval(pair, evaluator, differ, extractor,
                               preprocessor, onlyCachedOptions)

                self.logger.info(f"Report {old} and {new}.")

                return reporter.report(old, new, oldDist, newDist, oldDesc, newDesc, diff, bc)

    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 3, batcher: "Batcher | None" = None, options: "ProducerOptions | None" = None) -> "ProjectResult":
        """Batch process releases."""

        batcher = batcher or self.batcher
        assert isinstance(batcher, Batcher)

        with self.options.rewrite(options):
            with batcher.options.rewrite(self.options):
                if batcher.options.cancache:
                    try:
                        return batcher.fromcache(project)
                    except Exception as ex:
                        self.logger.warning(
                            f"Failed to load from cache.", exc_info=ex)

                self.logger.info(f"Batch process {project} releases.")

                return batcher.batch(project, workers, retry)

    def index(self, project: "str", workers: "int | None" = None, retry: "int" = 3, options: "ProducerOptions | None" = None) -> "ProjectResult":
        from aexpy.batching.loaders import BatchLoader
        loader = BatchLoader(provider=self.name)
        return self.batch(project, batcher=loader, workers=workers, retry=retry, options=options)

    def collect(self, pair: "ReleasePair", collector: "CollectorFunc | Collector", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None):
        """Collect processed data."""

        if not isinstance(collector, Collector):
            collector = FuncCollector(self.logger, collector)

        self.report(pair, collector, evaluator,
                    differ, extractor, preprocessor)

