from .models import Release, Distribution, ApiDescription, ApiDifference, ApiBreaking
from .preprocessing import Preprocessor, getDefault as getDefaultPreprocessor
from .extracting import Extractor, getDefault as getDefaultExtractor
from .differing import Differ, getDefault as getDefaultDiffer
from .evaluating import Evaluator, getDefault as getDefaultEvaluator


class Pipeline:
    def __init__(self, preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None) -> None:
        self.preprocessor = preprocessor or getDefaultPreprocessor()
        self.extractor = extractor or getDefaultExtractor()
        self.differ = differ or getDefaultDiffer()
        self.evaluator = evaluator or getDefaultEvaluator()

    def preprocess(self, release: "Release", preprocessor: "Preprocessor | None" = None) -> "Distribution":
        preprocessor = preprocessor or self.preprocessor
        return preprocessor.preprocess(release)

    def extract(self, release: "Release", extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiDescription":
        extractor = extractor or self.extractor
        return extractor.extract(self.preprocess(release, preprocessor))

    def diff(self, old: "Release", new: "Release", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiDifference":
        differ = differ or self.differ
        return differ.diff(self.extract(old, extractor, preprocessor), self.extract(new, extractor, preprocessor))

    def eval(self, old: "Release", new: "Release", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiBreaking":
        evaluator = evaluator or self.evaluator
        return evaluator.eval(self.diff(old, new, differ, extractor, preprocessor))
