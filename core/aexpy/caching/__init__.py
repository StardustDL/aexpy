from abc import ABC, abstractmethod
from pathlib import Path

from ..utils import ensureDirectory
from ..models import Product


class ProduceCache(ABC):
    def __init__(self, id: str) -> None:
        super().__init__()
        self.id = id

    @abstractmethod
    def save(self, product: Product, log: str) -> None:
        pass

    @abstractmethod
    def data(self) -> Product:
        pass

    @abstractmethod
    def log(self) -> str:
        pass


class FileProduceCache(ProduceCache):
    def __init__(self, id: str, cacheFile: Path):
        super().__init__(id)
        self.cacheFile = cacheFile
        # self.logFile = self.cacheFile.with_suffix(".log")

    def save(self, product: Product, log: str):
        ensureDirectory(self.cacheFile.parent)
        self.cacheFile.write_text(product.dumps())
        # self.logFile.write_text(log)

    def data(self):
        return self.cacheFile.read_text()

    def log(self):
        # return self.logFile.read_text()
        pass
