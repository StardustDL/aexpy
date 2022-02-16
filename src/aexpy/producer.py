from contextlib import contextmanager
import logging
from abc import ABC
from logging import Logger
from pathlib import Path

from aexpy import getCacheDirectory, utils


class Producer(ABC):
    def id(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    def stage(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}".split(".")[1]

    @property
    def cache(self):
        return self._cache

    @cache.setter
    def cache(self, value: Path):
        self._cache = value
        utils.ensureDirectory(self.cache)

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False) -> None:
        self.logger = logger.getChild(
            self.id()) if logger else logging.getLogger(self.id())
        self.cache = cache or getCacheDirectory() / self.stage()
        self.redo = redo

    @contextmanager
    def withRedo(self, redo: "bool | None" = None):
        if redo is None:
            yield self
        else:
            self._oldRedo = self.redo
            self.redo = redo

            yield self

            self.redo = self._oldRedo
            del self._oldRedo
