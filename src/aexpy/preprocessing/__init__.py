from abc import abstractmethod

from ..models import Distribution
from ..producers import Producer


class Preprocessor(Producer):
    @abstractmethod
    def preprocess(self, /, product: Distribution):
        """Preprocess a distribution."""
        ...


PYVERSION_UPPER = 12
PYVERSION_LOWER = 8
