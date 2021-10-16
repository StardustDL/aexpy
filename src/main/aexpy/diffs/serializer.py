from typing import Dict
from ..analyses.models import ApiCollection, ApiEntry, ApiManifest, FunctionEntry, FieldEntry, ClassEntry, Location, ModuleEntry, Parameter, ParameterKind, SpecialEntry, SpecialKind
from ..analyses import serializer as apiserializer
from .models import DiffCollection, DiffEntry
from enum import Enum
import json


def serialize(collection: DiffCollection, **kwargs) -> str:
    return json.dumps(collection, default=apiserializer.jsonify, **kwargs)


def deserialize(text) -> DiffCollection:
    raw = json.loads(text)
    entries: Dict[str, ApiEntry] = {}
    for key, entry in raw["entries"].items():
        old = entry.pop("old")
        new = entry.pop("new")
        entries[key] = DiffEntry(
            old=apiserializer.deserializeApiEntry(old),
            new=apiserializer.deserializeApiEntry(new),
            **entry)
    return DiffCollection(raw["old"], raw["new"], entries)
