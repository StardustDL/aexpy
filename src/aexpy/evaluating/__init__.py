from pathlib import Path
from ..producer import DefaultProducer, NoCachedProducer, Producer
from abc import ABC, abstractmethod
from ..models import ApiDifference, ApiBreaking


class Evaluator(Producer):
    @abstractmethod
    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        pass


class DefaultEvaluator(Evaluator, DefaultProducer):
    def getCacheFile(self, diff: "ApiDifference") -> "Path | None":
        return self.cache / diff.old.release.project / f"{diff.old.release}&{diff.new.release}.json"

    def getProduct(self, diff: "ApiDifference") -> "ApiBreaking":
        return ApiBreaking(old=diff.old, new=diff.new)

    def process(self, product: "ApiBreaking", diff: "ApiDifference"):
        pass

    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        return self.produce(diff=diff)


def getDefault() -> "Evaluator":
    from .default import Evaluator
    return Evaluator()


class _Empty(DefaultEvaluator, NoCachedProducer):
    def process(self, product: "ApiBreaking", diff: "ApiDifference"):
        product.entries = diff.entries.copy()


def getEmpty() -> "Evaluator":
    return _Empty()
