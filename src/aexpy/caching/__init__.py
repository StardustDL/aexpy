from abc import ABC, abstractmethod
from ..models import Product


class ProduceCacheManager(ABC):
    @abstractmethod
    def get(self, id: "str") -> "ProduceCache": pass

    @abstractmethod
    def submanager(self, id: "str") -> "ProduceCacheManager": pass


class ProduceCache(ABC):
    def __init__(self, id: "str", manager: "ProduceCacheManager") -> None:
        super().__init__()
        self.id = id
        self.manager = manager

    @abstractmethod
    def save(self, product: "Product", log: str) -> None: pass

    @abstractmethod
    def data(self) -> "Product": pass

    @abstractmethod
    def log(self) -> str: pass
