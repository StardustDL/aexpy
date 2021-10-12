import pathlib
from . import fsutils

class Environment:
    def __init__(self, path: pathlib.Path) -> None:
        self.setPath(path)

    def setPath(self, path: pathlib.Path) -> None:
        self.path = path
        self.cache = path.joinpath("cache")
    
    def prepare(self):
        fsutils.ensureDirectory(self.cache)


env: Environment = Environment(pathlib.Path("."))