import logging
import importlib
import pkgutil
import platform
import sys

from aexpy import initializeLogging
from aexpy.models import ApiDescription, Distribution, Release
from aexpy.models.description import (
    EXTERNAL_ENTRYID,
    TRANSFER_BEGIN,
    ApiEntry,
    AttributeEntry,
    ClassEntry,
    CollectionEntry,
    FunctionEntry,
    ItemScope,
    Location,
    ModuleEntry,
    Parameter,
    ParameterKind,
    SpecialEntry,
    SpecialKind,
    isPrivate
)
from aexpy.utils import getModuleName, getObjectId, isFunction

from . import Processor

def importModule(name: str):
    logger = logging.getLogger("import")
    logger.debug(f"Import {name}.")

    module = importlib.import_module(name)

    modules = [module]

    def onerror(name):
        logger.error(f"Failed to import {name}")

    try:
        for sub in pkgutil.walk_packages(
            path=module.__path__, prefix=module.__name__ + ".", onerror=onerror
        ):
            try:
                logger.debug(f"Import {sub[1]}.")
                submodule = importlib.import_module(sub[1])
                logger.debug(f"Imported {sub[1]}: {submodule}.")
                modules.append(submodule)
            except Exception as ex:
                logger.error(f"Failed to import {sub[1]}", exc_info=ex)
            except SystemExit as ex:
                logger.error(f"Failed to import {sub[1]}", exc_info=ex)
    except Exception as ex:
        logger.error(f"Failed to import {name}", exc_info=ex)
    except SystemExit as ex:
        logger.error(f"Failed to import {name}", exc_info=ex)

    return modules


def resolveAlias(api: ApiDescription):
    alias: "dict[str, set[str]]" = {}
    working: "set[str]" = set()

    def resolve(entry: ApiEntry):
        if entry.id in alias:
            return alias[entry.id]
        ret: "set[str]" = set()
        ret.add(entry.id)
        working.add(entry.id)
        for item in api.entries.values():
            if not isinstance(item, CollectionEntry):
                continue
            itemalias = None
            # ignore submodules and subclasses
            if item.id.startswith(f"{entry.id}."):
                continue
            for name, target in item.members.items():
                if target == entry.id:
                    if itemalias is None:
                        if item.id in working:  # cycle reference
                            itemalias = {item.id}
                        else:
                            itemalias = resolve(item)
                    for aliasname in itemalias:
                        ret.add(f"{aliasname}.{name}")
        alias[entry.id] = ret
        working.remove(entry.id)
        return ret

    for entry in api.entries.values():
        entry.alias = list(resolve(entry) - {entry.id})


def main(dist: Distribution):
    logger = logging.getLogger("main")

    platformStr = f"{platform.platform()} {platform.machine()} {platform.processor()} {platform.python_implementation()} {platform.python_version()}"
    logging.info(f"Platform: {platformStr}")

    result = ApiDescription()

    processor = Processor(result)

    successToplevels = []

    for topLevel in dist.topModules:
        modules = None

        try:
            logger.info(f"Import module {topLevel}.")

            modules = importModule(topLevel)
        except Exception as ex:
            logger.error(f"Failed to import module {topLevel}.", exc_info=ex)
            modules = None

        if modules:
            try:
                logger.info(f"Extract {topLevel} ({modules}).")

                processor.process(modules[0], modules)

                successToplevels.append(topLevel)
            except Exception as ex:
                logger.error(f"Failed to extract {topLevel}: {modules}.", exc_info=ex)

    assert len(successToplevels) > 0, "No top level module extracted."

    resolveAlias(result)
    for item in result.entries.values():
        if isPrivate(item):
            item.private = True

    return result


if __name__ == "__main__":
    initializeLogging(logging.NOTSET)
    dist = Distribution.model_validate_json(sys.stdin.read())

    assert dist.rootPath

    sys.path.insert(0, str(dist.rootPath.resolve()))

    output = main(dist).model_dump_json()
    print(TRANSFER_BEGIN, end="")
    print(output)
