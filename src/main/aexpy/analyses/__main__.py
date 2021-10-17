import logging
import sys
import os
import importlib
import pathlib
import subprocess
from . import serializer, PACKAGE_Dir, UNPACKED_Dir, STUB_Dir
from .models import ApiCollection

logging.basicConfig(level=logging.INFO)
importLogger = logging.getLogger("import")

modules = []

def import_module(name: str):
    importLogger.info(f"Import {name}.")

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
                    try:
                        import_module(".".join([name, submodule]))
                    except Exception as ex:
                        importLogger.error(ex)

    return module


def main(packageFile, topLevelModule):
    logger = logging.getLogger("main")

    file = PACKAGE_Dir.joinpath(packageFile)

    logger.info(f"Package file: {file}")

    logger.info("Install package.")

    installResult = subprocess.run(["pip", "install", str(file.absolute())],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    logger.info(installResult.stdout)
    logger.info(installResult.stderr)
    installResult.check_returncode()

    # logger.info("Generate stubs.")
    # stubgenResult = subprocess.run(["stubgen", "-p", topLevelModule, "-o", str(STUB_Dir.absolute())],
    #                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    # logger.info(stubgenResult.stdout)
    # logger.info(stubgenResult.stderr)
    # stubgenResult.check_returncode()

    topModule = import_module(topLevelModule)

    from .analyzer import Analyzer

    ana = Analyzer()

    return ana.process(topModule, modules)


if __name__ == "__main__":
    _, packageFile, topLevelModule = sys.argv
    result = main(packageFile, topLevelModule)
    print(serializer.serialize(result))
