import json
import logging
from enum import Enum
from typing import Dict

from .models import (ApiCollection, ApiEntry, ApiManifest, AttributeEntry,
                     ClassEntry, FunctionEntry, Location, ModuleEntry,
                     Parameter, ParameterKind, SpecialEntry, SpecialKind)

logger = logging.getLogger("analysis-serializer")


def _filter_obj_dict(x):
    res = {}
    for k, v in x.__dict__.items():
        if str(k).startswith("_"):
            continue
        res[k] = v
    return res


def jsonify(x):
    if isinstance(x, FunctionEntry):
        return {
            "schema": "func",
            **_filter_obj_dict(x)
        }
    elif isinstance(x, AttributeEntry):
        return {
            "schema": "attr",
            **_filter_obj_dict(x)
        }
    elif isinstance(x, ClassEntry):
        return {
            "schema": "class",
            **_filter_obj_dict(x)
        }
    elif isinstance(x, ModuleEntry):
        return {
            "schema": "module",
            **_filter_obj_dict(x)
        }
    elif isinstance(x, SpecialEntry):
        return {
            "schema": "special",
            **_filter_obj_dict(x)
        }
    elif isinstance(x, ApiManifest):
        return _filter_obj_dict(x)
    elif isinstance(x, Enum):
        return x.value
    return _filter_obj_dict(x)


def serialize(collection: ApiCollection, **kwargs) -> str:
    logger.info("Serializing")
    return json.dumps(collection, default=jsonify, **kwargs)


def deserializeApiEntry(entry: Dict) -> ApiEntry:
    schema = entry.pop("schema")
    data: Dict = entry
    locationData: Dict = data.pop("location")
    if schema == "attr":
        binded = AttributeEntry(**data)
    elif schema == "module":
        binded = ModuleEntry(**data)
    elif schema == "class":
        binded = ClassEntry(**data)
    elif schema == "func":
        paras = data.pop("parameters")
        bindedParas = []
        for para in paras:
            kind = ParameterKind(para.pop("kind"))
            bindedParas.append(Parameter(kind=kind, **para))
        binded = FunctionEntry(parameters=bindedParas, **data)
    elif schema == "special":
        kind = SpecialKind(data.pop("kind"))
        binded = SpecialEntry(kind=kind, **data)
    assert isinstance(binded, ApiEntry)
    binded.location = Location(**locationData)
    return binded


def deserialize(text) -> ApiCollection:
    logger.info("Deserializing")
    raw = json.loads(text)
    manifest = ApiManifest(**raw["manifest"])
    return ApiCollection(manifest, {key: deserializeApiEntry(entry) for key, entry in raw["entries"].items()})
