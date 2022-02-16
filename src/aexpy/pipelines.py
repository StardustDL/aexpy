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
        dist = self.preprocess(release, preprocessor)
        if not dist.success:
            raise ValueError(f"Failed to preprocess {release.name}")
        return extractor.extract(dist)

    def diff(self, old: "Release", new: "Release", differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiDifference":
        differ = differ or self.differ
        oldDes = self.extract(old, extractor, preprocessor)
        if not oldDes.success:
            raise ValueError(f"Failed to extract {old.name}")
        newDes = self.extract(new, extractor, preprocessor)
        if not newDes.success:
            raise ValueError(f"Failed to extract {new.name}")
        return differ.diff(oldDes, newDes)

    def eval(self, old: "Release", new: "Release", evaluator: "Evaluator | None" = None, differ: "Differ | None" = None, extractor: "Extractor | None" = None, preprocessor: "Preprocessor | None" = None) -> "ApiBreaking":
        evaluator = evaluator or self.evaluator
        diff = self.diff(old, new, differ, extractor, preprocessor)
        if not diff.success:
            raise ValueError(f"Failed to diff {old.name} and {new.name}")
        return evaluator.eval(diff)
