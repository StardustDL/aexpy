from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import IntEnum
from pathlib import Path
from typing import override
from pydantic import BaseModel, Field

from .description import (
    ApiEntry,
    AttributeEntry,
    ClassEntry,
    FunctionEntry,
    ItemScope,
    ModuleEntry,
    Parameter,
    ApiEntryType,
    SpecialEntry,
)
from .difference import BreakingRank, DiffEntry


class Release(BaseModel):
    project: str = ""
    version: str = ""

    def __str__(self):
        return f"{self.project}@{self.version}"

    @classmethod
    def fromId(cls, id: str):
        sp = id.split("@", maxsplit=1)
        if len(sp) == 1:
            return cls(project=sp[0])
        else:
            return cls(project=sp[0], version=sp[1])


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
    dependencies: list[str] = []

    @override
    def overview(self):
        return (
            super().overview()
            + f"""
  📦 {self.wheelFile}
  📁 {self.rootPath} ({self.fileCount} files, {self.fileSize} bytes, {self.locCount} LOC)
  🔖 {self.pyversion}
  📚 {', '.join(self.topModules)}
  🔩 {'\n     '.join(self.dependencies)}"""
        )

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

    modules: dict[str, ModuleEntry] = {}
    classes: dict[str, ClassEntry] = {}
    functions: dict[str, FunctionEntry] = {}
    attributes: dict[str, AttributeEntry] = {}
    specials: dict[str, SpecialEntry] = {}

    def __contains__(self, id: str):
        return (
            id in self.modules
            or id in self.classes
            or id in self.functions
            or id in self.attributes
            or id in self.specials
        )

    def __getitem__(self, id: str):
        return (
            self.modules.get(id)
            or self.classes.get(id)
            or self.functions.get(id)
            or self.attributes.get(id)
            or self.specials.get(id)
        )

    def __iter__(self):
        yield from self.modules.values()
        yield from self.classes.values()
        yield from self.functions.values()
        yield from self.attributes.values()
        yield from self.specials.values()

    def __len__(self):
        return (
            len(self.modules)
            + len(self.classes)
            + len(self.functions)
            + len(self.attributes)
            + len(self.specials)
        )

    @override
    def overview(self):
        return (
            super().overview()
            + f"""
  💠 {len(self)} entries
    Modules: {len(self.modules)}
    Classes: {len(self.classes)}
    Functions: {len(self.functions)}
    Attributes: {len(self.attributes)}"""
        )

    @override
    def single(self):
        assert self.distribution is not None
        return self.distribution.single()

    def resolveName(self, name: str):
        if name in self:
            return self[name]
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
                    return self[target]
        return None

    def resolveClassMember(self, cls: ClassEntry, name: str):
        result = None
        for mro in cls.mros:
            if result:
                return result
            base = self[mro]
            if isinstance(base, ClassEntry):
                if name in base.members:
                    target = base.members[name]
                    result = self[target]

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
        if entry.id in self:
            raise ValueError(f"Duplicate entry id {entry.id}")
        if isinstance(entry, ModuleEntry):
            self.modules[entry.id] = entry
        elif isinstance(entry, ClassEntry):
            self.classes[entry.id] = entry
        elif isinstance(entry, FunctionEntry):
            self.functions[entry.id] = entry
        elif isinstance(entry, AttributeEntry):
            self.attributes[entry.id] = entry
        elif isinstance(entry, SpecialEntry):
            self.specials[entry.id] = entry
        else:
            raise Exception(f"Unknown entry type: {entry.__class__} of {entry}")

    def clearCache(self):
        for cacheName in ["_names"]:
            if hasattr(self, cacheName):
                delattr(self, cacheName)

    def calcCallers(self):
        callers: dict[str, set[str]] = {}

        for item in self.functions.values():
            for callee in item.callees:
                if callee not in self:
                    continue
                if callee not in callers:
                    callers[callee] = set()
                callers[callee].add(item.id)

        for callee, caller in callers.items():
            entry = self[callee]
            if isinstance(entry, FunctionEntry):
                entry.callers = list(caller)

        self.clearCache()

    def calcSubclasses(self):
        subclasses: dict[str, set[str]] = {}

        for item in self.classes.values():
            for base in item.bases:
                if base not in self:
                    continue
                if base not in subclasses:
                    subclasses[base] = set()
                subclasses[base].add(item.id)

        for base, subclass in subclasses.items():
            entry = self[base]
            if isinstance(entry, ClassEntry):
                entry.subclasses = list(subclass)

        self.clearCache()

    @property
    def names(self):
        if hasattr(self, "_names"):
            return self._names
        self._names: "dict[str, list[ApiEntry]]" = {}
        for item in self:
            if item.name in self._names:
                self._names[item.name].append(item)
            else:
                self._names[item.name] = [item]
        return self._names


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
