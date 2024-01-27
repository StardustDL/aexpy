from abc import ABC, abstractmethod
from io import UnsupportedOperation
from pathlib import Path
from typing import IO, override

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
    def raw(self) -> str:
        pass

    @abstractmethod
    def log(self) -> str:
        pass

    def data[T: Product](self, cls: type[T]):
        return cls.model_validate_json(self.raw())


class FileProduceCache(ProduceCache):
    def __init__(self, id: str, cacheFile: Path, logFile: Path | None = None):
        super().__init__(id)
        self.cacheFile = cacheFile
        self.logFile = logFile

    @override
    def save(self, product, log):
        ensureDirectory(self.cacheFile.parent)
        self.cacheFile.write_text(product.model_dump_json())
        if self.logFile:
            self.logFile.write_text(log)

    @override
    def raw(self):
        return self.cacheFile.read_text()

    @override
    def log(self):
        return self.logFile.read_text() if self.logFile else ""


class StreamReaderProduceCache(ProduceCache):
    def __init__(self, stream: IO[str]):
        super().__init__("")
        self.stream = stream
        self.rawStr = None

    @override
    def save(self, product, log):
        raise UnsupportedOperation("Reader cache cannot save.")

    @override
    def raw(self):
        if self.rawStr is None:
            self.rawStr = self.stream.read()
        return self.rawStr

    @override
    def log(self):
        return ""


class StreamWriterProduceCache(ProduceCache):
    def __init__(self, cacheStream: IO[str], logStream: IO[str] | None = None):
        super().__init__("")
        self.cacheStream = cacheStream
        self.logStream = logStream

    @override
    def save(self, product, log):
        self.cacheStream.write(product.model_dump_json())
        if self.logStream:
            self.logStream.write(log)

    @override
    def raw(self):
        raise UnsupportedOperation("Writer cache cannot load.")

    @override
    def log(self):
        raise UnsupportedOperation("Writer cache cannot load.")
