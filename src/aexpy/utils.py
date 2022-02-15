import os
import pathlib
from typing import IO
from contextlib import contextmanager
from timeit import default_timer


class TeeFile(object):
    def __init__(self, *files: IO[str]):
        self.files = files

    def write(self, txt):
        for fp in self.files:
            fp.write(txt)


def ensureDirectory(path: pathlib.Path) -> None:
    path = path.absolute()
    if path.exists() and path.is_dir():
        return

    os.makedirs(path, exist_ok=True)


def ensureFile(path: pathlib.Path, content: str | None = None) -> None:
    path = path.absolute()
    if path.exists() and path.is_file():
        if content is not None:
            path.write_text(content)
        return

    ensureDirectory(path.parent)

    if content is None:
        content = ""

    path.write_text(content)


@contextmanager
def elapsedTimer():
    start = default_timer()
    def elapser(): return default_timer() - start
    yield lambda: elapser()
    end = default_timer()
    def elapser(): return end-start
