from ..models import Distribution, Release
from . import Preprocessor as Base


class Preprocessor(Base):
    def preprocess(self, release: "Release") -> "Distribution":
        raise NotImplementedError()
