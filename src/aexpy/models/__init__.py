import dataclasses
import json
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from logging import Logger
from pathlib import Path
from aexpy import getCacheDirectory

from aexpy.utils import elapsedTimer, ensureDirectory, logWithFile

from .description import (ApiEntry, AttributeEntry, ClassEntry, FunctionEntry,
                          ModuleEntry, Parameter, SpecialEntry, jsonifyEntry,
                          loadEntry)
from .difference import BreakingRank, DiffEntry


@dataclass
class Release:
    project: "str"
    version: "str"

    def __repr__(self) -> "str":
        return f"{self.project}@{self.version}"

    @classmethod
    def fromId(cls, id: "str") -> "Release":
        project, version = id.split("@")
        return cls(project, version)


@dataclass
class ReleasePair:
    old: "Release"
    new: "Release"

    def __repr__(self) -> str:
        if self.old.project == self.new.project:
            return f"{self.old.project}@{self.old.version}:{self.new.version}"
        else:
            return f"{self.old.project}@{self.old.version}:{self.new.project}@{self.new.version}"

    @classmethod
    def fromId(cls, id: "str") -> "ReleasePair":
        old, new = id.split(":")
        old = Release.fromId(old)
        if "@" in new:
            new = Release.fromId(new)
        else:
            new = Release(old.project, new)
        return cls(old, new)


def _jsonify(obj):
    if isinstance(obj, ApiEntry):
        return jsonifyEntry(obj)
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, timedelta):
        return obj.total_seconds()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif is_dataclass(obj):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    elif isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Cannot jsonify {obj}")


@dataclass
class Product:
    creation: "datetime | None" = None
    duration: "timedelta | None" = None
    logFile: "Path | None" = None
    success: "bool" = True

    def overview(self) -> "str":
        return f"""{'✅' if self.success else '❌'} {self.__class__.__name__} overview:
  ⏰ {self.creation} ⏱ {self.duration.total_seconds()}s
  📝 {self.logFile}"""

    def dumps(self, **kwargs):
        return json.dumps(self.__dict__, default=_jsonify, **kwargs)

    def load(self, data: "dict"):
        if "creation" in data and data["creation"] is not None:
            self.creation = datetime.fromisoformat(data.pop("creation"))
        if "duration" in data and data["duration"] is not None:
            self.duration = timedelta(seconds=data.pop("duration"))
        if "logFile" in data and data["logFile"] is not None:
            self.logFile = Path(data.pop("logFile"))
        if "success" in data:
            self.success = data.pop("success")

    def safeload(self, data: "dict"):
        """Load data into self and keep integrity when failed."""
        temp = self.__class__()
        temp.load(data)
        for field in dataclasses.fields(self):
            setattr(self, field.name, getattr(temp, field.name))

    @contextmanager
    def produce(self, cacheFile: "Path | None" = None, logger: "Logger | None" = None, logFile: "Path | None" = None, redo: "bool" = False, onlyCache: "bool" = False):
        """
        Provide a context to produce product.

        It will automatically use cached file, measure duration, and log to logFile if provided.

        If field duration, creation is None, it will also set them.
        """

        logger = logger or logging.getLogger(self.__class__.__qualname__)
        if cacheFile:
            ensureDirectory(cacheFile.parent)
            if logFile is None:
                logFile = cacheFile.with_suffix(".log")

        needProcess = not cacheFile or not cacheFile.exists() or redo

        if not needProcess:
            try:
                self.safeload(json.loads(cacheFile.read_text()))
            except Exception as ex:
                logger.error(
                    f"Failed to produce {self.__class__.__qualname__} by loading cache file {cacheFile}, will reproduce", exc_info=ex)
                needProcess = True

        if needProcess:
            if onlyCache:
                raise Exception(
                    f"{self.__class__.__qualname__} is not cached, cannot produce.")

            self.success = True
            self.creation = None  # To force recreation

            with logWithFile(logger, logFile):
                with elapsedTimer() as elapsed:
                    logger.info(f"Producing {self.__class__.__qualname__}.")
                    logger.info(f"Cache file: {cacheFile}")
                    logger.info(f"Log file: {logFile}")
                    try:
                        yield self

                        logger.info(f"Produced {self.__class__.__qualname__}.")
                    except Exception as ex:
                        logger.error(
                            f"Failed to produce {self.__class__.__qualname__}.", exc_info=ex)
                        self.success = False
                if self.duration is None:
                    self.duration = elapsed()

            if self.creation is None:
                self.creation = datetime.now()

            self.logFile = logFile
            if cacheFile:
                cacheFile.write_text(self.dumps())
        else:
            try:
                yield self
            except Exception as ex:
                logger.error(
                    f"Failed to produce {self.__class__.__qualname__} after loading from cache.", exc_info=ex)
                self.success = False


@dataclass
class SingleProduct(Product, ABC):
    @abstractmethod
    def single(self) -> "Release":
        pass

    def overview(self) -> "str":
        return super().overview().replace("overview", f"{self.single()}", 1)


@dataclass
class PairProduct(Product, ABC):
    @abstractmethod
    def pair(self) -> "ReleasePair":
        pass

    def overview(self) -> "str":
        return super().overview().replace("overview", f"{self.pair()}", 1)


@dataclass
class Distribution(SingleProduct):
    release: "Release | None" = None
    wheelFileRel: "Path | None" = None
    wheelDirRel: "Path | None" = None
    pyversion: "str" = "3.7"
    topModules: "list[str]" = field(default_factory=list)

    def overview(self) -> "str":
        return super().overview() + f"""
  📦 {self.wheelFile}
  📁 {self.wheelDir}
  🔖 {self.pyversion}
  📚 {', '.join(self.topModules)}"""

    def single(self) -> "Release":
        return self.release

    def load(self, data: "dict"):
        super().load(data)
        if "release" in data and data["release"] is not None:
            self.release = Release(**data.pop("release"))
        if "wheelFileRel" in data and data["wheelFileRel"] is not None:
            self.wheelFileRel = Path(data.pop("wheelFileRel"))
        if "wheelDirRel" in data and data["wheelDirRel"] is not None:
            self.wheelDirRel = Path(data.pop("wheelDirRel"))
        if "pyversion" in data and data["pyversion"] is not None:
            self.pyversion = data.pop("pyversion")
        if "topModules" in data and data["topModules"] is not None:
            self.topModules = data.pop("topModules")

    @property
    def wheelFile(self) -> "Path | None":
        if self.wheelFileRel is None:
            return None
        return getCacheDirectory().joinpath(self.wheelFileRel)

    @wheelFile.setter
    def wheelFile(self, value: "Path | None"):
        if value is None:
            self.wheelFileRel = None
        else:
            self.wheelFileRel = value.relative_to(getCacheDirectory())

    @property
    def wheelDir(self) -> "Path | None":
        if self.wheelDirRel is None:
            return None
        return getCacheDirectory().joinpath(self.wheelDirRel)

    @wheelDir.setter
    def wheelDir(self, value: "Path | None"):
        if value is None:
            self.wheelDirRel = None
        else:
            self.wheelDirRel = value.relative_to(getCacheDirectory())

    @property
    def src(self) -> "list[Path]":
        return [self.wheelDir / item for item in self.topModules]


@dataclass
class ApiDescription(SingleProduct):
    distribution: "Distribution | None" = None

    entries: "dict[str, ApiEntry]" = field(default_factory=dict)

    def overview(self) -> "str":
        return super().overview() + f"""
  💠 {len(self.entries)} entries
    Modules: {len(self.modules)}
    Classes: {len(self.classes)}
    Functions: {len(self.funcs)}
    Attributes: {len(self.attrs)}"""

    def single(self) -> "Release":
        return self.distribution.single()

    def load(self, data: "dict"):
        super().load(data)
        if "distribution" in data and data["distribution"] is not None:
            self.distribution = Distribution()
            self.distribution.load(data.pop("distribution"))
        if "entries" in data:
            for entry in data.pop("entries").values():
                self.addEntry(loadEntry(entry))

    def addEntry(self, entry: "ApiEntry") -> None:
        if entry.id in self.entries:
            raise ValueError(f"Duplicate entry id {entry.id}")
        self.entries[entry.id] = entry

    def clearCache(self) -> None:
        for cacheName in ["_names", "_modules", "_classes", "_funcs", "_attrs"]:
            if hasattr(self, cacheName):
                delattr(self, cacheName)

    @property
    def names(self) -> "dict[str, list[ApiEntry]]":
        if hasattr(self, "_names"):
            return self._names
        self._names: "dict[str, list[ApiEntry]]" = {}
        for item in self.entries.values():
            if item.name in self._names:
                self._names[item.name].append(item)
            else:
                self._names[item.name] = [item]
        return self._names

    @property
    def modules(self) -> "dict[str, ModuleEntry]":
        if hasattr(self, "_modules"):
            return self._modules
        self._modules = {
            k: v for k, v in self.entries.items() if isinstance(v, ModuleEntry)
        }
        return self._modules

    @property
    def classes(self) -> "dict[str, ClassEntry]":
        if hasattr(self, "_classes"):
            return self._classes
        self._classes = {
            k: v for k, v in self.entries.items() if isinstance(v, ClassEntry)
        }
        return self._classes

    @property
    def funcs(self) -> "dict[str, FunctionEntry]":
        if hasattr(self, "_funcs"):
            return self._funcs
        self._funcs = {
            k: v for k, v in self.entries.items() if isinstance(v, FunctionEntry)
        }
        return self._funcs

    @property
    def attrs(self) -> "dict[str, AttributeEntry]":
        if hasattr(self, "_attrs"):
            return self._attrs
        self._attrs = {
            k: v for k, v in self.entries.items() if isinstance(v, AttributeEntry)
        }
        return self._attrs


@dataclass
class ApiDifference(PairProduct):
    old: "Distribution | None" = None
    new: "Distribution | None" = None
    entries: "dict[str, DiffEntry]" = field(default_factory=dict)

    def overview(self) -> "str":
        kinds = self.kinds()

        kindstr = ''.join(
            f'\n    {kind}: {len(self.kind(kind))}' for kind in kinds)

        return super().overview() + f"""
  💠 {len(self.entries)} entries
  🆔 {len(kinds)} kinds{kindstr}"""

    def pair(self) -> "ReleasePair":
        return ReleasePair(self.old.single(), self.new.single())

    def load(self, data: "dict"):
        super().load(data)
        if "old" in data and data["old"] is not None:
            self.old = Distribution()
            self.old.load(data.pop("old"))
        if "new" in data and data["new"] is not None:
            self.new = Distribution()
            self.new.load(data.pop("new"))
        if "entries" in data:
            for key, value in data.pop("entries").items():
                old = loadEntry(
                    value.pop("old")) if "old" in value else None
                new = loadEntry(
                    value.pop("new")) if "new" in value else None
                rank = BreakingRank(
                    value.pop("rank")) if "rank" in value else BreakingRank.Unknown
                self.entries[key] = DiffEntry(
                    **value, old=old, new=new, rank=rank)

    def kind(self, name: "str"):
        return [x for x in self.entries.values() if x.kind == name]

    def kinds(self):
        return list({x.kind for x in self.entries.values()})


@dataclass
class ApiBreaking(ApiDifference):
    def evaluate(self) -> "tuple[BreakingRank, dict[BreakingRank, int]]":
        changesCount: "dict[BreakingRank, int]" = {}
        level = None
        for item in reversed(BreakingRank):
            items = self.rank(item)
            if items:
                if not level:
                    level = item
                changesCount[item] = len(items)
        level = level or BreakingRank.Compatible
        return level, changesCount

    def overview(self) -> "str":
        from aexpy.reporting.generators.text import BCIcons, BCLevel

        level, changesCount = self.evaluate()

        bcstr = ''.join(
            [f'\n    {BCIcons[rank]} {changesCount[rank]}' for rank in sorted(changesCount.keys(), reverse=True)])

        return super().overview() + f"""
  {BCLevel[level]} {level.name}{bcstr}"""

    def rank(self, rank: "BreakingRank") -> "list[DiffEntry]":
        return [x for x in self.entries.values() if x.rank == rank]

    def breaking(self, rank: "BreakingRank") -> "list[DiffEntry]":
        return [x for x in self.entries.values() if x.rank >= rank]


@ dataclass
class Report(PairProduct):
    old: "Release | None" = None
    new: "Release | None" = None
    fileRel: "Path | None" = None

    def overview(self) -> "str":
        return super().overview() + f"""
  📜 {self.file}"""

    def pair(self) -> "ReleasePair":
        return ReleasePair(self.old, self.new)

    def load(self, data: "dict"):
        super().load(data)
        if "old" in data and data["old"] is not None:
            self.old = Release(**data.pop("old"))
        if "new" in data and data["new"] is not None:
            self.new = Release(**data.pop("new"))
        if "fileRel" in data and data["fileRel"] is not None:
            self.fileRel = Path(data.pop("fileRel"))

    @property
    def file(self) -> "Path | None":
        if self.fileRel is None:
            return None
        return getCacheDirectory().joinpath(self.fileRel)

    @file.setter
    def file(self, value: "Path | None"):
        if value is None:
            self.fileRel = None
        else:
            self.fileRel = value.relative_to(getCacheDirectory())
