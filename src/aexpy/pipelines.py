import logging
from .models import Release, Distribution, ApiDescription, ApiDifference, ApiBreaking, ReleasePair, Report
from .preprocessing import Preprocessor, getDefault as getDefaultPreprocessor, getEmpty as getEmptyPreprocessor
from .extracting import Extractor, getDefault as getDefaultExtractor, getEmpty as getEmptyExtractor
from .differing import Differ, getDefault as getDefaultDiffer, getEmpty as getEmptyDiffer
from .evaluating import Evaluator, getDefault as getDefaultEvaluator, getEmpty as getEmptyEvaluator
from .reporting import Reporter, getDefault as getDefaultReporter, getEmpty as getEmptyReporter
from logging import Logger


class Pipeline:
    """Pipeline."""

    def __init__(self, preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Reporter | None" = None, redo: "bool | None" = None, cached: "bool | None" = None, logger: "Logger | None" = None) -> None:
        self.preprocessor = preprocessor or getDefaultPreprocessor()
        self.extractor = extractor or getDefaultExtractor()
        self.differ = differ or getDefaultDiffer()
        self.evaluator = evaluator or getDefaultEvaluator()
        self.reporter = reporter or getDefaultReporter()

        self.redo = redo
        """Redo, if all pre stage success, then redo current stage, else redo pre stage and current stage."""

        self.cached = cached
        """Cached."""

        self.logger = logger or logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}")

    def preprocess(self, release: "Release", preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> "Distribution":
        """Preprocess release."""

        self.logger.info(f"Preprocess {release}.")

        preprocessor = preprocessor or self.preprocessor
        redo = self.redo if redo is None else redo
        cached = self.cached if cached is None else cached

        with preprocessor.options.rewrite(redo, cached):
            return preprocessor.preprocess(release)

    def extract(self, release: "Release", extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> "ApiDescription":
        """Extract release."""

        extractor = extractor or self.extractor
        redo = self.redo if redo is None else redo
        cached = self.cached if cached is None else cached

        try:
            dist = self.preprocess(release, preprocessor)
            assert dist.success, f"Failed to preprocess {release}"
        except:
            if not redo:
                raise
            else:
                dist = self.preprocess(release, preprocessor, redo=True)
                if not dist.success:
                    raise
        
        self.logger.info(f"Extract {release}.")

        with extractor.options.rewrite(redo, cached):
            return extractor.extract(dist)

    def diff(self, pair: "ReleasePair", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> "ApiDifference":
        """Diff old and new release."""

        differ = differ or self.differ
        redo = self.redo if redo is None else redo
        cached = self.cached if cached is None else cached

        old, new = pair.old, pair.new

        try:
            oldDes = self.extract(old, extractor, preprocessor)
            assert oldDes.success, f"Failed to extract {old}"
        except:
            if not redo:
                raise
            else:
                oldDes = self.extract(old, extractor, preprocessor, redo=True)
                if not oldDes.success:
                    raise

        try:
            newDes = self.extract(new, extractor, preprocessor)
            assert newDes.success, f"Failed to extract {new}"
        except:
            if not redo:
                raise
            else:
                newDes = self.extract(new, extractor, preprocessor, redo=True)
                if not newDes.success:
                    raise
        
        self.logger.info(f"Diff {old} and {new}.")

        with differ.options.rewrite(redo, cached):
            return differ.diff(oldDes, newDes)

    def eval(self, pair: "ReleasePair", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> "ApiBreaking":
        """Evaluate old and new release."""

        evaluator = evaluator or self.evaluator
        redo = self.redo if redo is None else redo
        cached = self.cached if cached is None else cached

        old, new = pair.old, pair.new

        try:
            diff = self.diff(pair, differ, extractor, preprocessor)
            assert diff.success, f"Failed to diff {old} and {new}"
        except:
            if not redo:
                raise
            else:
                diff = self.diff(pair, differ, extractor,
                                 preprocessor, redo=True)
                if not diff.success:
                    raise

        self.logger.info(f"Evaluate {old} and {new}.")

        with evaluator.options.rewrite(redo, cached):
            return evaluator.eval(diff)

    def report(self, pair: "ReleasePair", reporter: "Reporter | None" = None, evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> "Report":
        """Report breaking changes between old and new release."""

        reporter = reporter or self.reporter
        redo = self.redo if redo is None else redo
        cached = self.cached if cached is None else cached

        old, new = pair.old, pair.new

        try:
            bc = self.eval(pair, evaluator, differ,
                           extractor, preprocessor)
            assert bc.success, f"Failed to evaluate {old} and {new}"
        except:
            if not redo:
                raise
            else:
                bc = self.eval(pair, evaluator, differ,
                               extractor, preprocessor, redo=True)
                if not bc.success:
                    raise

        oldDist = self.preprocess(old, preprocessor)
        newDist = self.preprocess(new, preprocessor)
        oldDesc = self.extract(old, extractor, preprocessor)
        newDesc = self.extract(new, extractor, preprocessor)
        diff = self.diff(pair, differ, extractor, preprocessor)
        bc = self.eval(pair, evaluator, differ, extractor, preprocessor)

        self.logger.info(f"Report {old} and {new}.")

        with reporter.options.rewrite(redo, cached):
            return reporter.report(old, new, oldDist, newDist, oldDesc, newDesc, diff, bc)


class EmptyPipeline(Pipeline):
    def __init__(self, preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Reporter | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> None:
        super().__init__(preprocessor or getEmptyPreprocessor(), extractor or getEmptyExtractor(),
                         differ or getEmptyDiffer(), evaluator or getEmptyEvaluator(), reporter or getEmptyReporter(), redo, cached)
