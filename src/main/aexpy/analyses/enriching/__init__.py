from abc import ABC, abstractmethod

from ..models import ApiCollection


class Enricher(ABC):
    @abstractmethod
    def enrich(api: ApiCollection):
        pass
