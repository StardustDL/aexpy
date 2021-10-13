import sys
import importlib

if __name__ == "__main__":
    _, packageFile, topLevelModule = sys.argv

    print(f"Package file: {packageFile}")

    topModule = importlib.import_module(topLevelModule)

    print(topModule)