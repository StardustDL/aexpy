import logging
import importlib
import pkgutil
import platform
import sys
from typing import Union, List

from .compat import (
    Distribution,
    ModuleEntry,
    ClassEntry,
    FunctionEntry,
    AttributeEntry,
    SpecialEntry,
)

from .processor import Processor

TRANSFER_BEGIN = "AEXPY_TRANSFER_BEGIN"


LOGGING_FORMAT = "%(levelname)s %(asctime)s %(name)s [%(pathname)s:%(lineno)d:%(funcName)s]\n%(message)s\n"
LOGGING_DATEFMT = "%Y-%m-%d,%H:%M:%S"


def initializeLogging(level: int = logging.WARNING) -> None:
    root = logging.getLogger()
    root.setLevel(logging.NOTSET)
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOGGING_FORMAT, LOGGING_DATEFMT))
    root.addHandler(handler)


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
            submoduleName = sub[1]
            if submoduleName.endswith(".__main__"):
                logger.debug(f"Ignore {submoduleName}.")
                continue
            try:
                logger.debug(f"Import {submoduleName}.")
                submodule = importlib.import_module(submoduleName)
                logger.debug(f"Imported {submoduleName}: {submodule}.")
                modules.append(submodule)
            except Exception as ex:
                logger.error(f"Failed to import {submoduleName}", exc_info=ex)
            except SystemExit as ex:
                logger.error(f"Failed to import {submoduleName}", exc_info=ex)
    except Exception as ex:
        logger.error(f"Failed to import {name}", exc_info=ex)
    except SystemExit as ex:
        logger.error(f"Failed to import {name}", exc_info=ex)

    return modules


def main(dist: Distribution):
    logger = logging.getLogger("main")

    platformStr = f"{platform.platform()} {platform.machine()} {platform.processor()} {platform.python_implementation()} {platform.python_version()}"
    logging.info(f"Platform: {platformStr}")

    processor = Processor()

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

    return processor.allEntries()


if __name__ == "__main__":
    initializeLogging(logging.NOTSET)
    dist = Distribution.model_validate_json(sys.stdin.read())

    assert dist.rootPath

    sys.path.insert(0, str(dist.rootPath.resolve()))

    from pydantic import TypeAdapter

    output = TypeAdapter(
        List[
            Union[ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry, SpecialEntry]
        ]
    ).dump_json(main(dist))
    print(TRANSFER_BEGIN, end="")
    print(output.decode())
