from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path


from ..models import ApiDescription, Distribution, ProduceCache, Product, Release
from ..producers import (Producer, ProducerOptions)


class Extractor(Producer):
    def extract(self, dist: "Distribution", product: "ApiDescription"):
        """Extract an API description from a distribution."""
        pass
