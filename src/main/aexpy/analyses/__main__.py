import sys
import os
import importlib
import pathlib
import subprocess
from . import serializer
from .models import ApiCollection

PACKAGE_Dir = pathlib.Path("/package")
UNPACKED_Dir = PACKAGE_Dir.joinpath("unpacked")


def main(packageFile, topLevelModule):
    file = PACKAGE_Dir.joinpath(packageFile)
    subprocess.run(["pip", "install", str(file.absolute())], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    topModule = importlib.import_module(topLevelModule)
    return ApiCollection()


if __name__ == "__main__":
    _, packageFile, topLevelModule = sys.argv
    result = main(packageFile, topLevelModule)
    print(serializer.serialize(result))
