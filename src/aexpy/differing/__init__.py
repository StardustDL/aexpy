from pathlib import Path
from ..producer import DefaultProducer, NoCachedProducer, Producer
from abc import ABC, abstractmethod
from ..models import ApiDifference, ApiDescription


class Differ(Producer):
    @abstractmethod
    def diff(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
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


class _Empty(DefaultDiffer, NoCachedProducer):
    pass


def getEmpty() -> "Differ":
    return _Empty()
