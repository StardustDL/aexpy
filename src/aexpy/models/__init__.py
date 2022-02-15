from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import timedelta, datetime
from enum import Enum
from pathlib import Path
from .description import ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, SpecialEntry, AttributeEntry, Parameter, jsonifyEntry, loadEntry
from .difference import DiffEntry
import json


@dataclass
class Release:
    project: "str"
    version: "str"


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
        return asdict(obj)
    raise TypeError(f"Cannot jsonify {obj}")


@dataclass
class Product:
    creation: "datetime | None" = None
    duration: "timedelta | None" = None
    logFile: "Path | None" = None
    success: "bool" = True

    def dumps(self, **kwargs):
        return json.dumps(asdict(self), default=_jsonify, **kwargs)

    def load(self, data: "dict"):
        if "creation" in data and data["creation"] is not None:
            self.creation = datetime.fromisoformat(data.pop("creation"))
        if "duration" in data and data["duration"] is not None:
            self.duration = timedelta(seconds=data.pop("duration"))
        if "logFile" in data and data["logFile"] is not None:
            self.logFile = Path(data.pop("logFile"))
        if "success" in data:
            self.success = data.pop("success")


@dataclass
class Distribution(Product):
    release: "Release | None" = None
    wheelFile: "Path | None" = None
    wheelDir: "Path | None" = None
    pyversion: "str" = "3.7"
    topModules: "list[str]" = field(default_factory=list)

    def load(self, data: "dict"):
        super().load(data)
        if "release" in data and data["release"] is not None:
            self.release = Release(**data.pop("release"))
        if "wheelFile" in data and data["wheelFile"] is not None:
            self.wheelFile = Path(data.pop("wheelFile"))
        if "wheelDir" in data and data["wheelDir"] is not None:
            self.wheelDir = Path(data.pop("wheelDir"))
        if "pyversion" in data and data["pyversion"] is not None:
            self.pyversion = data.pop("pyversion")
        if "topModules" in data and data["topModules"] is not None:
            self.topModules = data.pop("topModules")

    @property
    def src(self) -> "list[Path]":
        return [self.wheelDir / item for item in self.topModules]


@dataclass
class ApiDescription(Product):
    distribution: "Distribution | None" = None

    entries: "dict[str, ApiEntry]" = field(default_factory=dict)

    def load(self, data: "dict"):
        super().load(data)
        if "distribution" in data and data["distribution"] is not None:
            self.distribution = Distribution()
            self.distribution.load(data.pop("distribution"))
        if "entries" in data:
            for entry in data.pop("entries"):
                self.addEntry(loadEntry(entry))

    def addEntry(self, entry: "ApiEntry") -> None:
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
class ApiDifference(Product):
    old: "Distribution | None" = None
    new: "Distribution | None" = None
    entries: "dict[str, DiffEntry]" = field(default_factory=dict)

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
                old = loadEntry(value.pop("old")) if "old" in value else None
                new = loadEntry(value.pop("new")) if "new" in value else None
                self.entries[key] = DiffEntry(**value, old=old, new=new)

    def kind(self, name: "str"):
        return [x for x in self.entries.values() if x.kind == name]

    def kinds(self):
        return list({x.kind for x in self.entries.values()})


@dataclass
class ApiBreaking(ApiDifference):
    pass
