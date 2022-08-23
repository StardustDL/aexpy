from abc import ABC, abstractmethod
from ..models import Product
from pathlib import Path
from ..utils import ensureDirectory
from . import ProduceCache, ProduceCacheManager


class FileProduceCacheManager(ProduceCacheManager):
    def __init__(self, cacheDir: "Path") -> None:
        super().__init__()
        self.cacheDir = cacheDir

    def get(self, id: "str") -> "ProduceCache":
        return FileProduceCache(id, self, self.cacheDir.joinpath(f"{id}.json"))

    def submanager(self, id: "str") -> "ProduceCacheManager":
        return FileProduceCacheManager(self.cacheDir.joinpath(id))


class FileProduceCache(ProduceCache):
    def __init__(self, id: "str", manager: "ProduceCacheManager", cacheFile: "Path") -> None:
        super().__init__(id, manager)
        self.cacheFile = cacheFile
        self.logFile = self.cacheFile.with_suffix(".log")

    def save(self, product: "Product", log: "str") -> None:
        ensureDirectory(self.cacheFile.parent)
        self.cacheFile.write_text(product.dumps())
        self.logFile.write_text(log)

    def data(self) -> "str":
        return self.cacheFile.read_text()

    def log(self) -> str:
        return self.logFile.read_text()
