from typing import Dict
from .models import ApiCollection, ApiManifest, FunctionEntry, FieldEntry, ClassEntry, ModuleEntry, Parameter, ParameterKind, SpecialEntry, SpecialKind
from enum import Enum
import json


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
            "data": _filter_obj_dict(x)
        }
    elif isinstance(x, FieldEntry):
        return {
            "schema": "field",
            "data": _filter_obj_dict(x)
        }
    elif isinstance(x, ClassEntry):
        return {
            "schema": "class",
            "data": _filter_obj_dict(x)
        }
    elif isinstance(x, ModuleEntry):
        return {
            "schema": "module",
            "data": _filter_obj_dict(x)
        }
    elif isinstance(x, SpecialEntry):
        return {
            "schema": "special",
            "data": _filter_obj_dict(x)
        }
    elif isinstance(x, ApiManifest):
        return _filter_obj_dict(x)
    elif isinstance(x, Enum):
        return x.value
    return _filter_obj_dict(x)


def serialize(collection: ApiCollection) -> str:
    return json.dumps(collection, default=jsonify, indent=4)


def deserialize(text) -> ApiCollection:
    raw = json.loads(text)
    manifest = ApiManifest(**raw["manifest"])
    entries = []
    for entry in raw["entries"]:
        schema = entry["schema"]
        data: Dict = entry["data"]
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
        entries.append(binded)
    return ApiCollection(manifest, entries)



if __name__ == "__main__":
    collection = ApiCollection()
    collection.entries.append(SpecialEntry("extenal", "extenal", SpecialKind.External, "data"))
    collection.entries.append(ModuleEntry("module", "module", {
        "func": "func",
        "class": "class"
    }))
    collection.entries.append(ClassEntry("class", "class", ["base"], {
        "func": "func"
    }))
    collection.entries.append(FunctionEntry("func", "func", False, "None", [
        Parameter(ParameterKind.Positional, "para", "str", "empty", True),
    ]))


    text = serialize(collection)
    print(text)

    raw = deserialize(text)

    assert raw.entries[0].kind is SpecialKind.External
    assert raw.entries[3].parameters[0].kind is ParameterKind.Positional

    print(serialize(raw))

    assert serialize(raw) == text