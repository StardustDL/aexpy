import importlib
import logging
import os
import pathlib
import platform
import subprocess
import sys

from . import (LOGGING_DATEFMT, LOGGING_FORMAT, OUTPUT_PREFIX, PACKAGE_Dir,
               STUB_Dir, UNPACKED_Dir, serializer)
from .models import ApiCollection

importLogger = logging.getLogger("import")

modules = []


def import_module(name: str):
    importLogger.debug(f"Import {name}.")

    module = importlib.import_module(name)

    modules.append(module)

    file = getattr(module, "__file__", None)

    if file:
        file = pathlib.Path(file)
        if file.name == "__init__.py":
            for submodulefile in file.parent.iterdir():
                submodule = None
                if submodulefile.is_dir():
                    if submodulefile.joinpath("__init__.py").exists():
                        submodule = pathlib.Path(submodulefile).stem
                else:
                    if not submodulefile.name.startswith("_") and submodulefile.suffix == ".py":
                        submodule = pathlib.Path(submodulefile).stem
                if submodule:
                    moduleName = ".".join([name, submodule])
                    try:
                        import_module(moduleName)
                    except Exception as ex:
                        importLogger.error(
                            f"Failed to import {moduleName}", exc_info=ex)
                    except SystemExit as ex:
                        importLogger.error(
                            f"Failed to import {moduleName}", exc_info=ex)

    return module


def main(packageFile, topLevelModule):
    logger = logging.getLogger("main")

    file = PACKAGE_Dir.joinpath(packageFile)

    logger.info(f"Package file: {file}")

    logger.info("Install package.")

    installResult = subprocess.run(["pip", "install", str(file.absolute())],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    if installResult.returncode != 0:
        logger.error(f"Failed to install {file}")
        logger.warning(f"STDOUT: {installResult.stdout}")
        logger.error(f"STDERR: {installResult.stderr}")
        installResult.check_returncode()

    # logger.info("Generate stubs.")
    # stubgenResult = subprocess.run(["stubgen", "-p", topLevelModule, "-o", str(STUB_Dir.absolute())],
    #                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    # logger.info(stubgenResult.stdout)
    # logger.info(stubgenResult.stderr)
    # stubgenResult.check_returncode()

    logger.info(f"Import module {topLevelModule}.")

    topModule = import_module(topLevelModule)

    from .analyzer import Analyzer

    ana = Analyzer()

    logger.info(f"Analyze {topLevelModule} and {modules}.")

    return ana.process(topModule, modules)


if __name__ == "__main__":
    _, packageFile, topLevelModule, verbose = sys.argv

    verbose = int(verbose)

    loggingLevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
        4: logging.NOTSET
    }[verbose]

    logging.basicConfig(level=loggingLevel,
                        format=LOGGING_FORMAT, datefmt=LOGGING_DATEFMT)

    logger = logging.getLogger("init")

    platformStr = f"{platform.platform()} {platform.machine()} {platform.processor()} {platform.python_implementation()} {platform.python_version()}"

    logging.info(f"Platform: {platformStr}")

    result = main(packageFile, topLevelModule)
    result.manifest.wheel = packageFile
    result.manifest.platform = platformStr
    print(OUTPUT_PREFIX, end="")
    print(serializer.serialize(result))
