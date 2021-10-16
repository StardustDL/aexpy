import logging
import sys
import os
import importlib
import pathlib
import subprocess
from . import serializer, PACKAGE_Dir, UNPACKED_Dir, STUB_Dir
from .models import ApiCollection

logging.basicConfig(level=logging.INFO)


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

    logger.info("Generate stubs.")
    stubgenResult = subprocess.run(["stubgen", "-p", topLevelModule, "-o", str(STUB_Dir.absolute())],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    logger.info(stubgenResult.stdout)
    logger.info(stubgenResult.stderr)
    stubgenResult.check_returncode()

    topModule = importlib.import_module(topLevelModule)

    from .analyzer import Analyzer

    ana = Analyzer()

    return ana.process(topModule)


if __name__ == "__main__":
    _, packageFile, topLevelModule = sys.argv
    result = main(packageFile, topLevelModule)
    print(serializer.serialize(result))
