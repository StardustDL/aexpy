from .models import Release, Distribution, ApiDescription, ApiDifference, ApiBreaking
from .preprocessing import Preprocessor, getDefault as getDefaultPreprocessor
from .extracting import Extractor, getDefault as getDefaultExtractor
from .differing import Differ, getDefault as getDefaultDiffer
from .evaluating import Evaluator, getDefault as getDefaultEvaluator


def preprocess(release: "Release", preprocessor: "Preprocessor | None" = None) -> "Distribution":
    preprocessor = preprocessor or getDefaultPreprocessor()
    return preprocessor.preprocess(release)


def extract(release: "Release", extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiDescription":
    extractor = extractor or getDefaultExtractor()
    return extractor.extract(preprocessor(release, preprocessor))


def diff(old: "Release", new: "Release", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiDifference":
    differ = differ or getDefaultDiffer()
    return differ.diff(extract(old, extractor, preprocessor), extract(new, extractor, preprocessor))


def eval(old: "Release", new: "Release", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiBreaking":
    evaluator = evaluator or getDefaultEvaluator()
    return evaluator.eval(diff(old, new, differ, extractor, preprocessor))