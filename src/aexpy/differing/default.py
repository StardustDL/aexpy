from ..models import ApiDifference, Distribution, ApiDescription
from . import Differ as Base


class Differ(Base):
    def diff(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
        raise NotImplementedError()
