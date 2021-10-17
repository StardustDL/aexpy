from dataclasses import dataclass, field
import pathlib
from . import fsutils
from . import get_app_directory

@dataclass
class DockerEnvironment:
    enable: bool = False
    hostCache: pathlib.Path = field(default_factory=lambda:pathlib.Path("./cache"))
    hostSrc: pathlib.Path = field(default_factory=lambda:get_app_directory())


class Environment:
    def __init__(self, path: pathlib.Path) -> None:
        self.setPath(path)
        self.dev = True
        self.docker = DockerEnvironment()

    def setPath(self, path: pathlib.Path) -> None:
        self.path = path
        self.cache = path.joinpath("cache")
    
    def prepare(self):
        fsutils.ensureDirectory(self.cache)


env: Environment = Environment(pathlib.Path("."))