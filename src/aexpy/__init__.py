import logging
import os
import pathlib

import click

__version__ = "0.0.1"


def getAppDirectory() -> pathlib.Path:
    return pathlib.Path(__file__).parent.resolve()


def getCacheDirectory() -> pathlib.Path:
    return (getAppDirectory().parent / "cache").resolve()
