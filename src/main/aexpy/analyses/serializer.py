import json
from enum import Enum
from typing import Dict

from .models import (ApiCollection, ApiEntry, ApiManifest, ClassEntry,
                     FieldEntry, FunctionEntry, Location, ModuleEntry,
                     Parameter, ParameterKind, SpecialEntry, SpecialKind)


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
    elif isinstance(x, FieldEntry):
        return {
            "schema": "field",
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
    return json.dumps(collection, default=jsonify, **kwargs)


def deserializeApiEntry(entry: Dict) -> ApiEntry:
    schema = entry.pop("schema")
    data: Dict = entry
    locationData: Dict = data.pop("location")
    if schema == "field":
        binded = FieldEntry(**data)
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
    raw = json.loads(text)
    manifest = ApiManifest(**raw["manifest"])
    return ApiCollection(manifest, {key: deserializeApiEntry(entry) for key, entry in raw["entries"].items()})


if __name__ == "__main__":
    collection = ApiCollection()
    collection.addEntry(SpecialEntry(
        "extenal", "extenal", None, SpecialKind.External, "data"))
    collection.addEntry(ModuleEntry("module", "module", None, {
        "func": "func",
        "class": "class"
    }))
    collection.addEntry(ClassEntry("class", "class", None, ["base"], {
        "func": "func"
    }))
    collection.addEntry(FunctionEntry("func", "func", None, False, "None", [
        Parameter(ParameterKind.Positional, "para", "str", "empty", True),
    ]))

    text = serialize(collection)
    print(text)

    raw = deserialize(text)

    assert raw.entries[0].kind is SpecialKind.External
    assert raw.entries[3].parameters[0].kind is ParameterKind.Positional

    print(serialize(raw))

    assert serialize(raw) == text
