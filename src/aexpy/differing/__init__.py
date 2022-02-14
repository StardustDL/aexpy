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
