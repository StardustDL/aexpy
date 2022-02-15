from abc import ABC
from logging import Logger
from pathlib import Path
import logging

from aexpy import utils, getCacheDirectory


class Producer(ABC):
    def id(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    def stage(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}".split(".")[1]

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False) -> None:
        self.logger = logger or logging.getLogger(self.id())
        self.cache = cache or getCacheDirectory() / self.stage()
        utils.ensureDirectory(self.cache)
        self.redo = redo
