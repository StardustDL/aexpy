from abc import ABC, abstractmethod
from pathlib import Path

from aexpy import getCacheDirectory

from ..models import (ApiBreaking, ApiDescription, ApiDifference, Distribution,
                      Product, Release)
from ..producer import (DefaultProducer, IncrementalProducer, NoCachedProducer, Producer,
                        ProducerOptions)


class Evaluator(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "evaluating"

    @abstractmethod
    def eval(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "ApiBreaking":
        pass

    def fromcache(self, old: "Release", new: "Release") -> "ApiBreaking":
        with self.options.rewrite(ProducerOptions(onlyCache=True)):
            old = Distribution(release=old)
            new = Distribution(release=new)
            return self.eval(ApiDifference(old=old, new=new), ApiDescription(distribution=old), ApiDescription(distribution=new))


class DefaultEvaluator(Evaluator, DefaultProducer):
    def getCacheFile(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "Path | None":
        return self.cache / diff.old.release.project / f"{diff.old.release}&{diff.new.release}.json"

    def getProduct(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "ApiBreaking":
        return ApiBreaking(old=diff.old, new=diff.new)

    def process(self, product: "ApiBreaking", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        pass

    def eval(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "ApiBreaking":
        return self.produce(diff=diff, old=old, new=new)


def getDefault() -> "Evaluator":
    from .verifiers import Verifier
    return Verifier()


class Empty(DefaultEvaluator, NoCachedProducer):
    def process(self, product: "ApiBreaking", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        product.entries = diff.entries.copy()

    def produce(self, *args, **kwargs) -> "Product":
        self.options.onlyCache = False
        self.options.nocache = True
        return super().produce(*args, **kwargs)


def getEmpty() -> "Evaluator":
    return Empty()


class IncrementalEvaluator(IncrementalProducer, DefaultEvaluator):
    @abstractmethod
    def basicProduce(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "ApiBreaking":
        pass

    def incrementalProcess(self, product: "ApiDescription", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        pass
