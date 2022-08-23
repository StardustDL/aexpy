from ..models import Distribution, Release
from ..producers import Producer


class Preprocessor(Producer):
    def preprocess(self, release: "Release", product: "Distribution"):
        """Preprocess a release and return a distribution."""
        pass
