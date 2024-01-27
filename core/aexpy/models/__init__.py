import dataclasses
import io
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING, override, Annotated
from pydantic import BaseModel, Field

from aexpy import json
from aexpy.utils import elapsedTimer, logWithStream

from .description import (
    ApiEntry,
    AttributeEntry,
    ClassEntry,
    FunctionEntry,
    ItemScope,
    ModuleEntry,
    Parameter,
    ApiEntryType,
    loadEntry,
)
from .difference import BreakingRank, DiffEntry, VerifyData, VerifyState

if TYPE_CHECKING:
    from aexpy.caching import ProduceCache

class ProduceMode(IntEnum):
    Access = 0
    """Read from cache if available, otherwise produce."""
    Read = 1
    """Read from cache."""
    Write = 2
    """Redo and write to cache."""


class Release(BaseModel):
    project: str = "unknown"
    version: str = "unknown"

    def __str__(self):
        return f"{self.project}@{self.version}"

    @classmethod
    def fromId(cls, id: str):
        project, version = id.split("@")
        return cls(project=project, version=version)


class ReleasePair(BaseModel):
    old: Release
    new: Release

    def __str__(self):
        if self.old.project == self.new.project:
            return f"{self.old.project}@{self.old.version}:{self.new.version}"
        else:
            return f"{self.old.project}@{self.old.version}:{self.new.project}@{self.new.version}"

    @classmethod
    def fromId(cls, id: str):
        old, new = id.split(":")
        old = Release.fromId(old)
        if "@" in new:
            new = Release.fromId(new)
        else:
            new = Release(project=old.project, version=new)
        return cls(old=old, new=new)


class ProduceState(IntEnum):
    Pending = 0
    Success = 1
    Failure = 2


class Product(BaseModel):
    creation: datetime = Field(default_factory=datetime.now)
    duration: timedelta = timedelta(seconds=0)
    producer: str = ""
    state: ProduceState = ProduceState.Pending

    @property
    def success(self):
        return self.state == ProduceState.Success

    def overview(self):
        return f"""{['⌛', '✅', '❌'][self.state]} {self.__class__.__name__} overview (by {self.producer}):
  ⏰ {self.creation} ⏱ {self.duration.total_seconds()}s"""

    def dumps(self):
        return self.model_dump_json()

    def load(self, data: dict):
        self.__init__(**data)

    def safeload(self, data: dict):
        """Load data into self and keep integrity when failed."""
        try:    
            self.__class__(**data)
            self.load(data)
        except:
            pass

    @contextmanager
    def increment(self):
        """
        Provide a context to produce incremental product, deleting inner elapsed time.
        """

        with elapsedTimer() as elapsed:
            try:
                yield self
            except:
                raise
            finally:
                self.duration -= elapsed()
                if self.duration.total_seconds() < 0:
                    self.duration = timedelta(seconds=0)

    @contextmanager
    def produce(
        self,
        cache: "ProduceCache",
        mode: ProduceMode = ProduceMode.Access,
        logger: Logger | None = None,
    ):
        """
        Provide a context to produce product.

        It will automatically use cached file, measure duration, and log to logFile if provided.

        If field duration, creation is None, it will also set them.
        """

        logger = logger or logging.getLogger(self.__class__.__qualname__)

        needProcess = mode == ProduceMode.Write

        if not needProcess:
            try:
                self.safeload(json.loads(cache.data()))
            except Exception as ex:
                logger.error(
                    f"Failed to produce {self.__class__.__qualname__} by loading cache, will reproduce",
                    exc_info=ex,
                )
                needProcess = True

        if needProcess:
            if mode == ProduceMode.Read:
                raise Exception(
                    f"{self.__class__.__qualname__} is not cached, cannot produce."
                )

            self.state = ProduceState.Pending

            logStream = io.StringIO()

            with logWithStream(logger, logStream):
                with elapsedTimer() as elapsed:
                    logger.info(f"Producing {self.__class__.__qualname__}.")
                    try:
                        yield self

                        self.state = ProduceState.Success
                        logger.info(f"Produced {self.__class__.__qualname__}.")
                    except Exception as ex:
                        logger.error(
                            f"Failed to produce {self.__class__.__qualname__}.",
                            exc_info=ex,
                        )
                        self.state = ProduceState.Failure
                self.duration += elapsed()

            self.creation = datetime.now()

            cache.save(self, logStream.getvalue())
        else:
            try:
                yield self
            except Exception as ex:
                logger.error(
                    f"Failed to produce {self.__class__.__qualname__} after loading from cache.",
                    exc_info=ex,
                )
                self.state = ProduceState.Failure

    @classmethod
    def fromCache(
        cls,
        cache: "ProduceCache",
        logger: Logger | None = None,
    ):
        product = cls()
        with product.produce(cache, ProduceMode.Read, logger=logger) as product:
            return product

class SingleProduct(Product, ABC):
    @abstractmethod
    def single(self) -> Release:
        pass

    @override
    def overview(self):
        return super().overview().replace("overview", f"{self.single()}", 1)


class PairProduct(Product, ABC):
    @abstractmethod
    def pair(self) -> ReleasePair:
        pass

    @override
    def overview(self):
        return super().overview().replace("overview", f"{self.pair()}", 1)


class Distribution(SingleProduct):
    release: Release = Release()
    wheelFile: Path | None = None
    rootPath: Path | None = None
    pyversion: str = ""
    topModules: list[str] = []
    fileCount: int = 0
    fileSize: int = 0
    locCount: int = 0
    metadata: list[tuple[str, str]] = []
    description: str = ""
    requirements: list[str] = []

    @override
    def overview(self):
        return super().overview() + f"""
  📦 {self.wheelFile}
  📁 {self.rootPath} ({self.fileCount} files, {self.fileSize} bytes, {self.locCount} LOC)
  🔖 {self.pyversion}
  📚 {', '.join(self.topModules)}"""

    @override
    def single(self):
        assert self.release is not None
        return self.release

    @property
    def src(self):
        assert self.rootPath is not None
        return [self.rootPath / item for item in self.topModules]



class ApiDescription(SingleProduct):
    distribution: Distribution = Distribution()

    entries: dict[str, Annotated[ApiEntryType, Field(discriminator="form")]] = {}

    @override
    def overview(self):
        return (
            super().overview()
            + f"""
  💠 {len(self.entries)} entries
    Modules: {len(self.modules)}
    Classes: {len(self.classes)}
    Functions: {len(self.funcs)}
    Attributes: {len(self.attrs)}"""
        )

    @override
    def single(self):
        assert self.distribution is not None
        return self.distribution.single()

    def resolveName(self, name: str):
        if name in self.entries:
            return self.entries[name]
        if "." not in name:
            return None
        parentName, memberName = name.rsplit(".", 1)
        if parentName and memberName:
            parent = self.resolveName(parentName)
            if isinstance(parent, ClassEntry):
                return self.resolveClassMember(parent, memberName)
            elif isinstance(parent, ModuleEntry):
                target = parent.members.get(memberName)
                if target:
                    return self.entries.get(target)
        return None

    def resolveClassMember(self, cls: ClassEntry, name: str):
        result = None
        for mro in cls.mros:
            if result:
                return result
            base = self.entries.get(mro)
            if isinstance(base, ClassEntry):
                if name in base.members:
                    target = base.members[name]
                    result = self.entries.get(target)

        if name == "__init__":
            return FunctionEntry(
                name="__init__",
                id="object.__init__",
                private=False,
                scope=ItemScope.Instance,
                parameters=[Parameter(name="self")],
            )

        return None

    def addEntry(self, entry: ApiEntryType):
        if entry.id in self.entries:
            raise ValueError(f"Duplicate entry id {entry.id}")
        self.entries[entry.id] = entry

    def clearCache(self):
        for cacheName in ["_names", "_modules", "_classes", "_funcs", "_attrs"]:
            if hasattr(self, cacheName):
                delattr(self, cacheName)

    def calcCallers(self):
        callers: dict[str, set[str]] = {}

        for item in self.funcs.values():
            for callee in item.callees:
                if callee not in self.entries:
                    continue
                if callee not in callers:
                    callers[callee] = set()
                callers[callee].add(item.id)

        for callee, caller in callers.items():
            entry = self.entries.get(callee)
            if isinstance(entry, FunctionEntry):
                entry.callers = list(caller)

        self.clearCache()

    @property
    def names(self):
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
    def modules(self):
        if hasattr(self, "_modules"):
            return self._modules
        self._modules = {
            k: v for k, v in self.entries.items() if isinstance(v, ModuleEntry)
        }
        return self._modules

    @property
    def classes(self):
        if hasattr(self, "_classes"):
            return self._classes
        self._classes = {
            k: v for k, v in self.entries.items() if isinstance(v, ClassEntry)
        }
        return self._classes

    @property
    def funcs(self):
        if hasattr(self, "_funcs"):
            return self._funcs
        self._funcs = {
            k: v for k, v in self.entries.items() if isinstance(v, FunctionEntry)
        }
        return self._funcs

    @property
    def attrs(self):
        if hasattr(self, "_attrs"):
            return self._attrs
        self._attrs = {
            k: v for k, v in self.entries.items() if isinstance(v, AttributeEntry)
        }
        return self._attrs


class ApiDifference(PairProduct):
    old: Distribution = Distribution()
    new: Distribution = Distribution()
    entries: dict[str, DiffEntry] = {}

    @override
    def overview(self):
        from aexpy.reporting.text import BCIcons, BCLevel

        level, changesCount = self.evaluate()

        bcstr = "".join(
            [
                f"\n    {BCIcons[rank]} {changesCount[rank]}"
                for rank in sorted(changesCount.keys(), reverse=True)
            ]
        )

        kinds = self.kinds()

        kindstr = "".join(f"\n    {kind}: {len(self.kind(kind))}" for kind in kinds)

        return (
            super().overview()
            + f"""
  💠 {len(self.entries)} entries
  🆔 {len(kinds)} kinds{kindstr}
  {BCLevel[level]} {level.name}{bcstr}"""
        )

    @override
    def pair(self):
        assert self.old and self.new
        return ReleasePair(old=self.old.single(), new=self.new.single())

    def kind(self, name: str):
        return [x for x in self.entries.values() if x.kind == name]

    def kinds(self):
        return list({x.kind for x in self.entries.values()})

    def evaluate(self):
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

    def rank(self, rank: BreakingRank):
        return [x for x in self.entries.values() if x.rank == rank]

    def breaking(self, rank: BreakingRank):
        return [x for x in self.entries.values() if x.rank >= rank]

    def verified(self):
        return [x for x in self.entries.values() if x.verify.state == VerifyState.Pass]



class Report(PairProduct):
    old: Distribution = Distribution()
    new: Distribution = Distribution()
    content: str = ""

    @override
    def overview(self):
        return super().overview()

    @override
    def pair(self):
        assert self.old and self.new
        return ReleasePair(old=self.old.release, new=self.new.release)
