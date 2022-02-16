from .models import Release, Distribution, ApiDescription, ApiDifference, ApiBreaking, Report
from .preprocessing import Preprocessor, getDefault as getDefaultPreprocessor, getEmpty as getEmptyPreprocessor
from .extracting import Extractor, getDefault as getDefaultExtractor, getEmpty as getEmptyExtractor
from .differing import Differ, getDefault as getDefaultDiffer, getEmpty as getEmptyDiffer
from .evaluating import Evaluator, getDefault as getDefaultEvaluator, getEmpty as getEmptyEvaluator
from .reporting import Reporter, getDefault as getDefaultReporter, getEmpty as getEmptyReporter


class Pipeline:
    def __init__(self, preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Reporter | None" = None, redo: "bool | None" = None) -> None:
        self.preprocessor = preprocessor or getDefaultPreprocessor()
        self.extractor = extractor or getDefaultExtractor()
        self.differ = differ or getDefaultDiffer()
        self.evaluator = evaluator or getDefaultEvaluator()
        self.reporter = reporter or getDefaultReporter()
        self.redo = redo

    def preprocess(self, release: "Release", preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None) -> "Distribution":
        preprocessor = preprocessor or self.preprocessor
        redo = redo or self.redo
        with preprocessor.withRedo(redo):
            return preprocessor.preprocess(release)

    def extract(self, release: "Release", extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None) -> "ApiDescription":
        extractor = extractor or self.extractor
        dist = self.preprocess(release, preprocessor)
        if not dist.success:
            raise ValueError(f"Failed to preprocess {release.name}")
        with extractor.withRedo(redo):
            return extractor.extract(dist)

    def diff(self, old: "Release", new: "Release", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None) -> "ApiDifference":
        differ = differ or self.differ
        oldDes = self.extract(old, extractor, preprocessor)
        if not oldDes.success:
            raise ValueError(f"Failed to extract {old.name}")
        newDes = self.extract(new, extractor, preprocessor)
        if not newDes.success:
            raise ValueError(f"Failed to extract {new.name}")
        with differ.withRedo(redo):
            return differ.diff(oldDes, newDes)

    def eval(self, old: "Release", new: "Release", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None) -> "ApiBreaking":
        evaluator = evaluator or self.evaluator
        diff = self.diff(old, new, differ, extractor, preprocessor)
        if not diff.success:
            raise ValueError(f"Failed to diff {old.name} and {new.name}")
        with evaluator.withRedo(redo):
            return evaluator.eval(diff)

    def report(self, old: "Release", new: "Release", reporter: "Reporter | None" = None, evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None, redo: "bool | None" = None) -> "Report":
        reporter = reporter or self.reporter
        bc = self.eval(old, new, evaluator, differ, extractor, preprocessor)
        if not bc.success:
            raise ValueError(f"Failed to eval {old.name} and {new.name}")

        oldDist = self.preprocess(old, preprocessor)
        newDist = self.preprocess(new, preprocessor)
        oldDesc = self.extract(old, extractor, preprocessor)
        newDesc = self.extract(new, extractor, preprocessor)
        diff = self.diff(old, new, differ, extractor, preprocessor)
        bc = self.eval(old, new, evaluator, differ, extractor, preprocessor)

        with reporter.withRedo(redo):
            return reporter.report(old, new, oldDist, newDist, oldDesc, newDesc, diff, bc)


class EmptyPipeline(Pipeline):
    def __init__(self, preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Reporter | None" = None,  redo: "bool | None" = None) -> None:
        super().__init__(preprocessor or getEmptyPreprocessor(), extractor or getEmptyExtractor(),
                         differ or getEmptyDiffer(), evaluator or getEmptyEvaluator(), reporter or getEmptyReporter(), redo)
