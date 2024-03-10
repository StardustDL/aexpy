import gzip
from abc import ABC, abstractmethod
from io import IOBase, UnsupportedOperation
from pathlib import Path
from typing import IO, Callable, Literal, overload, override

from ..models import (ApiDescription, ApiDifference, CoreProduct, Distribution,
                      Product, Report)
from ..utils import ensureDirectory


class ProductLoader(ABC):
    @abstractmethod
    def raw(self, /) -> bytes: ...

    @abstractmethod
    def log(self, /) -> bytes: ...

    def load[P: Product](self, /, cls: type[P]):
        return cls.model_validate_json(self.raw())


class ProductSaver(ABC):
    @abstractmethod
    def save(self, /, product: Product, log: str): ...


class FileProductIO(ProductLoader, ProductSaver):
    def __init__(self, /, target: Path, logFile: Path | None = None):
        super().__init__()
        self.target = target
        self.logFile = logFile

    def open(self, /, path: Path, write: bool = False):
        return path.open(mode="wb" if write else "rb")

    @override
    def save(self, /, product, log):
        ensureDirectory(self.target.parent)
        with self.open(self.target, write=True) as f:
            f.write(product.model_dump_json().encode())
        if self.logFile:
            with self.open(self.logFile, write=True) as f:
                f.write(log.encode())

    @override
    def raw(self, /):
        return self.target.read_bytes()

    @override
    def log(self, /):
        return self.logFile.read_bytes() if self.logFile else b""


class StreamProductLoader(ProductLoader):
    def __init__(self, /, stream: IO[bytes]):
        super().__init__()
        self.stream = stream
        self.rawData = None

    def read(self, /, stream: IO[bytes]):
        return stream.read()

    @override
    def raw(self, /):
        if self.rawData is None:
            self.rawData = self.read(self.stream)
        return self.rawData

    @override
    def log(self, /):
        return b""


class StreamProductSaver(ProductSaver):
    def __init__(self, /, target: IO[bytes], logStream: IO[bytes] | None = None):
        super().__init__()
        self.target = target
        self.logStream = logStream

    def write(self, /, stream: IO[bytes], data: bytes):
        stream.write(data)

    @override
    def save(self, /, product, log):
        self.write(self.target, product.model_dump_json().encode())
        if self.logStream:
            self.write(self.logStream, log.encode())


type LoadSourceType = Path | IOBase | bytes | str | dict


@overload
def load[T: Product](data: LoadSourceType, fallback: type[T]) -> T: ...


@overload
def load[
    T: Product
](data: LoadSourceType, fallback: Callable[[dict], T]) -> CoreProduct | T: ...


@overload
def load(data: LoadSourceType) -> CoreProduct: ...


def load[
    T: Product
](data: LoadSourceType, fallback: Callable[[dict], T] | type[T] | None = None):
    import gzip
    import json

    from ..models import ApiDescription, ApiDifference, Distribution, Report

    try:
        if isinstance(data, Path):
            data = data.read_bytes()
        if isinstance(data, IOBase):
            data = data.read()
        if isinstance(data, bytes):
            try:
                data = gzip.decompress(data)
            except gzip.BadGzipFile:
                pass
            data = data.decode()
        if isinstance(data, str):
            data = json.loads(data)
        assert isinstance(data, dict), f"Not a valid data type: {data}"

        if isinstance(fallback, type):
            return fallback.model_validate(data)
    except Exception as ex:
        raise Exception(f"Failed to read data") from ex

    try:
        if "release" in data:
            return Distribution.model_validate(data)
        elif "distribution" in data:
            return ApiDescription.model_validate(data)
        elif "entries" in data:
            return ApiDifference.model_validate(data)
        else:
            return Report.model_validate(data)
    except Exception as ex:
        if fallback:
            try:
                return fallback(data)
            except Exception as ex:
                raise Exception(f"Failed to load data") from ex
        else:
            raise Exception(f"Failed to load data") from ex
