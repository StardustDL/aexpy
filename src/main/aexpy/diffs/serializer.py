import json
from enum import Enum
import logging

from ..analyses import serializer as apiserializer
from ..analyses.models import (ApiCollection, ApiEntry, ApiManifest,
                               ClassEntry, AttributeEntry, FunctionEntry, Location,
                               ModuleEntry, Parameter, ParameterKind,
                               SpecialEntry, SpecialKind)
from .models import DiffCollection, DiffEntry

logger = logging.getLogger("diff-serializer")


def serialize(collection: DiffCollection, **kwargs) -> str:
    logger.info("Serializing")
    return json.dumps(collection, default=apiserializer.jsonify, **kwargs)


def deserialize(text) -> DiffCollection:
    logger.info("Deserializing")
    raw = json.loads(text)
    entries: dict[str, ApiEntry] = {}
    for key, entry in raw["entries"].items():
        old = entry.pop("old")
        new = entry.pop("new")
        entries[key] = DiffEntry(
            old=apiserializer.deserializeApiEntry(old) if old else None,
            new=apiserializer.deserializeApiEntry(new) if new else None,
            **entry)
    return DiffCollection(ApiManifest(**raw["old"]), ApiManifest(**raw["new"]), entries)
