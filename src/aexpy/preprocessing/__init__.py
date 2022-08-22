from abc import ABC, abstractmethod
from pathlib import Path

from aexpy import getCacheDirectory

from ..models import Distribution, ProduceCache, ProduceMode, Product, Release
from ..producers import Producer


class Preprocessor(Producer):
    def preprocess(self, release: "Release", product: "Distribution"):
        """Preprocess a release and return a distribution."""
        pass


def getDefault() -> "Preprocessor":
    from .pip import PipPreprocessor
    return PipPreprocessor(mirror=True)
