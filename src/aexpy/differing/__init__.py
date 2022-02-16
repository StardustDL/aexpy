from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import ApiDifference, ApiDescription


class Differ(Producer):
    @abstractmethod
    def diff(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
        pass


def getDefault() -> "Differ":
    from .default import Differ
    return Differ()


class _Empty(Differ):
    def diff(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
        with ApiDifference(old=old.distribution, new=new.distribution).produce(logger=self.logger, redo=self.redo) as diff:
            return diff


def getEmpty() -> "Differ":
    return _Empty()
