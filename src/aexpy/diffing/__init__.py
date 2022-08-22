from abc import ABC, abstractmethod
from pathlib import Path

from ..models import (ApiDescription, ApiDifference, Distribution, Product,
                      Release, ReleasePair)
from ..producers import (Producer,
                         ProducerOptions)


class Differ(Producer):
    def diff(self, old: "ApiDescription", new: "ApiDescription", product: "ApiDifference"):
        """Diff two versions of the API and return the differences."""
        pass
