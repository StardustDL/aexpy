import os
import pathlib
from typing import Optional


def ensureDirectory(path: pathlib.Path) -> None:
    path = path.absolute()
    if path.exists() and path.is_dir():
        return

    os.makedirs(path, exist_ok=True)


def ensureFile(path: pathlib.Path, content: Optional[str] = None) -> None:
    path = path.absolute()
    if path.exists() and path.is_file():
        if content is not None:
            path.write_text(content)
        return

    ensureDirectory(path.parent)

    if content is None:
        content = ""

    path.write_text(content)
