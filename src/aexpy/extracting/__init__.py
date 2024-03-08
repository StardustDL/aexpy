from abc import abstractmethod

from ..models import ApiDescription, Distribution
from ..producers import Producer


class Extractor(Producer):
    @abstractmethod
    def extract(self, /, dist: Distribution, product: ApiDescription):
        """Extract an API description from a distribution."""
        ...
