import logging
import os
import pathlib

__version__ = "0.0.1"


def getAppDirectory() -> pathlib.Path:
    return pathlib.Path(__file__).parent.resolve()


_cachePath = (getAppDirectory().parent / "cache").resolve()


def getCacheDirectory() -> pathlib.Path:
    return _cachePath


def setCacheDirectory(path: pathlib.Path) -> None:
    global _cachePath
    _cachePath = path
