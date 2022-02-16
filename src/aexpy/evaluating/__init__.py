from ..producer import Producer
from abc import ABC, abstractmethod
from ..models import ApiDifference, ApiBreaking


class Evaluator(Producer):
    @abstractmethod
    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        pass


def getDefault() -> "Evaluator":
    from .default import Evaluator
    return Evaluator()


class _Empty(Evaluator):
    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        with ApiBreaking(old=diff.old, new=diff.new).produce(logger=self.logger, redo=self.redo) as bc:
            return bc


def getEmpty() -> "Evaluator":
    return _Empty()
