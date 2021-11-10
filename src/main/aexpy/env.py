import pathlib
from dataclasses import dataclass, field

from . import fsutils, get_app_directory


@dataclass
class DockerEnvironment:
    enable: bool = False
    hostCache: pathlib.Path = field(
        default_factory=lambda: pathlib.Path("./cache").absolute())
    hostSrc: pathlib.Path = field(default_factory=lambda: get_app_directory())


class Environment:
    def __init__(self, path: pathlib.Path) -> None:
        self.setPath(path)
        self.dev = True
        self.redo = False
        self.interactive = False
        self.docker = DockerEnvironment()
        self.verbose = 0

    def setPath(self, path: pathlib.Path) -> None:
        self.path = path.absolute()
        self.cache = path.joinpath("cache").absolute()


env: Environment = Environment(pathlib.Path("."))
