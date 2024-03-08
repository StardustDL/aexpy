from abc import abstractmethod

from ..models import ApiDifference, Report
from ..producers import Producer


class Reporter(Producer):
    @abstractmethod
    def report(self, /, diff: ApiDifference, product: Report):
        """Report the differences between two versions of the API."""
        ...
