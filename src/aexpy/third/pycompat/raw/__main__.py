import importlib
import inspect
import logging
import pathlib
import platform
import sys
from datetime import datetime
from types import ModuleType

from aexpy import initializeLogging, json
from aexpy.models import ApiDescription, Distribution, Release
from aexpy.models.description import (TRANSFER_BEGIN, ApiEntry, AttributeEntry,
                                      ClassEntry, CollectionEntry,
                                      FunctionEntry, Location, ModuleEntry,
                                      Parameter, ParameterKind, SpecialEntry,
                                      SpecialKind)

from .library_traverser import MemberVisitor, traverse_module


def importModule(name: str) -> "ModuleType":
    logger = logging.getLogger("import")
    logger.debug(f"Import {name}.")

    module = importlib.import_module(name)

    import pkgutil

    sub_modules = [m for m in pkgutil.iter_modules(module.__path__) if m[2]]

    for m in sub_modules:
        try:
            importlib.import_module(f"{name}.{m[1]}", m)
        except Exception as ex:
            logger.error("Failed to import sub module %s.%s",
                         name, m[1], exc_info=ex)
        except SystemExit as ex:
            logger.error("Failed to import sub module %s.%s",
                         name, m[1], exc_info=ex)

    return module


def main(dist: "Distribution"):
    logger = logging.getLogger("main")

    result = ApiDescription()

    res = []

    successToplevels = []

    def visit(data):
        res.append(data)

    visitor = MemberVisitor(visit, inspect)

    for topLevel in dist.topModules:
        module = None
        try:
            logger.info(f"Import module {topLevel}.")

            module = importModule(topLevel)
        except Exception as ex:
            logger.error(f"Failed to import module {topLevel}.", exc_info=ex)
            module = None

        if module:
            try:
                logger.info(f"Extract {topLevel} ({module}).")

                traverse_module((topLevel, module), visitor, topLevel, {})

                successToplevels.append(topLevel)
            except Exception as ex:
                logger.error(
                    f"Failed to extract module {topLevel}: {module}.", exc_info=ex)
    
    assert len(successToplevels) > 0, "No top level module extracted."

    logger.debug("RAW OUTPUT:\n" + json.dumps(res))

    def getname(id):
        return id[id.rfind(".")+1:]

    def basic(entry: "ApiEntry", item: "dict[str, str]"):
        entry.id = item["_id"]
        entry.docs = item["doc"]
        entry.name = getname(entry.id)

    def func(entry: "FunctionEntry", item: "dict[str, str]"):
        basic(entry, item)
        entry.comments = item["signature"]
        entry.parameters = [Parameter(name=name, optional=p["is_optional"],
                                      default=p["default"]) for name, p in item["parameters"].items()]

    for item in res:
        entry = None
        try:
            if item["type"] == "module":
                entry = ModuleEntry()
            elif item["type"] == "class":
                entry = ClassEntry()
                for key in item["member_functions"]:
                    entry.members[getname(key)] = key
                for key in item["attributes"]:
                    entry.members[getname(key)] = key
            elif item["type"] == "member_function":
                entry = FunctionEntry()
                func(entry, item)
                entry.location = Location(module=item["class"])
            elif item["type"] == "field":
                entry = AttributeEntry()
                entry.location = Location(module=item["class"])
            elif item["type"] == "function":
                entry = FunctionEntry()
                func(entry, item)
            elif item["type"] == "module_field":
                entry = AttributeEntry()
                entry.location = Location(module=item["module"])
            else:
                logger.error(f"Unknown type {item['type']}: {item}")
            if entry:
                basic(entry, item)
        except Exception as ex:
            logger.error(f"Failed to create entry for {item}.", exc_info=ex)
            entry = None

        if entry:
            if "." in entry.id:
                entry.parent = entry.id.rsplit(".", 1)[0]
            result.addEntry(entry)

    return result


if __name__ == '__main__':
    initializeLogging(logging.NOTSET)
    dist = Distribution()
    dist.load(json.loads(sys.stdin.read()))

    output = main(dist).dumps()
    print(TRANSFER_BEGIN, end="")
    print(output)
