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
        utils.ensureDirectory(self._cache)

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, cached: "bool" = True) -> None:
        self.logger = logger.getChild(
            self.id()) if logger else logging.getLogger(self.id())
        self.cached = cached
        self.cache = cache or getCacheDirectory() / self.stage()
        self.redo = redo

    @contextmanager
    def withOption(self, redo: "bool | None" = None, cached: "bool | None" = None):
        if redo is not None:
            self._oldRedo = self.redo
            self.redo = redo
        if cached is not None:
            self._oldCached = self.cached
            self.cached = cached
        
        yield self

        if redo is not None:
            self.redo = self._oldRedo
            del self._oldRedo
        if cached is not None:
            self.cached = self._oldCached
            del self._oldCached
