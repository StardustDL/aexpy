from pathlib import Path

from aexpy import getCacheDirectory
from ..producer import DefaultProducer, Producer, NoCachedProducer, ProducerOptions
from abc import ABC, abstractmethod
from ..models import ApiDifference, ApiBreaking


class Evaluator(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "evaluating"

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


class Empty(DefaultEvaluator, NoCachedProducer):
    def process(self, product: "ApiBreaking", diff: "ApiDifference"):
        product.entries = diff.entries.copy()

def getEmpty() -> "Evaluator":
    return Empty()
