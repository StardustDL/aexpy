from ..models import ApiDifference, ApiBreaking
from . import Evaluator as Base


class Evaluator(Base):
    def eval(self, diff: ApiDifference) -> ApiBreaking:
        raise NotImplementedError()
