import gzip
from pathlib import Path
from typing import IO, BinaryIO, cast, override

from . import FileProductIO, StreamProductLoader, StreamProductSaver


class GzipStreamProductLoader(StreamProductLoader):
    def __init__(self, /, stream: IO[bytes]):
        super().__init__(stream)

    @override
    def read(self, /, stream):
        with gzip.open(stream) as f:
            return f.read()


class GzipStreamAutoProductLoader(StreamProductLoader):
    def __init__(self, /, stream: IO[bytes]):
        super().__init__(stream)

    @override
    def read(self, /, stream):
        data = stream.read()
        try:
            return gzip.decompress(data)
        except gzip.BadGzipFile:
            return data


class GzipStreamProductSaver(StreamProductSaver):
    def __init__(self, /, target: IO[bytes], logStream: IO[bytes] | None = None):
        super().__init__(target, logStream)

    @override
    def write(self, /, stream, data):
        with gzip.open(stream, mode="wb") as f:
            f.write(data)


class GzipFileProductIO(FileProductIO):
    def __init__(self, /, target: Path, logFile: Path | None = None):
        super().__init__(target, logFile)

    @override
    def open(self, /, path, write=False):
        return cast(BinaryIO, gzip.open(path, mode="wb" if write else "rb"))
