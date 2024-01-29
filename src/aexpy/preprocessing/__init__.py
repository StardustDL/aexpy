from ..models import Distribution, Release
from ..producers import Producer


class Preprocessor(Producer):
    def preprocess(self, product: Distribution):
        """Preprocess a distribution."""
        pass


PYVERSION_UPPER = 12
PYVERSION_LOWER = 8
