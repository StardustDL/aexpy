from abc import ABC, abstractmethod
from pathlib import Path

from ..models import (ApiDescription, ApiDifference, Distribution, Product,
                      Release, ReleasePair)
from ..producers import (Producer,
                        ProducerOptions)


class Differ(Producer):
    @abstractmethod
    def diff(self, old: "ApiDescription", new: "ApiDescription", product: "ApiDifference"):
        """Differ two versions of the API and return the differences."""
        pass

class DefaultDiffer(Differ, DefaultProducer):
    def getCacheFile(self, old: "ApiDescription", new: "ApiDescription") -> "Path | None":
        return self.cache / old.distribution.release.project / f"{old.distribution.release}&{new.distribution.release}.json"

    def getProduct(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
        return ApiDifference(old=old.distribution, new=new.distribution)

    def process(self, product: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        pass

    def diff(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
        return self.produce(old=old, new=new)


def getDefault() -> "Differ":
    from .default import Differ
    return Differ()


class Empty(DefaultDiffer, NoCachedProducer):
    def produce(self, *args, **kwargs) -> "Product":
        self.options.onlyCache = False
        self.options.nocache = True
        return super().produce(*args, **kwargs)


def getEmpty() -> "Differ":
    return Empty()
