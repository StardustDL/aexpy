from abc import abstractmethod
from logging import Logger
from pathlib import Path
import subprocess
import json
from typing import Callable
from uuid import uuid1

from aexpy.models import ApiDescription, Distribution
from . import Extractor, ExtractorEnvironment


class CondaEnvironment(ExtractorEnvironment):
    __baseenvprefix__ = "conda-extbase-"
    __envprefix__ = "conda-ext-"
    __packages__ = []

    def clearBase(self):
        self.reloadBase()
        for key, item in list(self.baseEnv.items()):
            subprocess.run(
                f"conda remove -n {item} --all -y -q", shell=True, check=True, capture_output=True)
            del self.baseEnv[key]

    def reloadBase(self):
        envs = json.loads(subprocess.run("conda env list --json", shell=True,
                          capture_output=True, text=True, check=True).stdout)["envs"]
        envs = [Path(item).name for item in envs]
        for item in envs:
            if item.startswith(self.__baseenvprefix__):
                self.baseEnv[item.removeprefix(self.__baseenvprefix__)] = item

    def __init__(self, pythonVersion: str = "3.7") -> None:
        super().__init__(pythonVersion)
        self.name = f"{self.__envprefix__}{self.pythonVersion}-{uuid1()}"
        self.baseEnv: "dict[str, str]" = {}

    def run(self, command: str, **kwargs):
        return subprocess.run(f"conda activate {self.name} && {command}", **kwargs, shell=True)

    def __enter__(self):
        if not self.baseEnv:
            self.reloadBase()
        if self.pythonVersion not in self.baseEnv:
            baseName = f"{self.__baseenvprefix__}{self.pythonVersion}"
            subprocess.run(
                f"conda create -n {baseName} python={self.pythonVersion} -y -q", shell=True, check=True, capture_output=True)
            if self.__packages__:
                subprocess.run(
                    f"conda activate {baseName} && python -m pip install {f' '.join(self.__packages__)}", shell=True, check=True, capture_output=True)
            self.baseEnv[self.pythonVersion] = baseName
        subprocess.run(
            f"conda create -n {self.name} --clone {self.baseEnv[self.pythonVersion]} -y -q", shell=True, check=True, capture_output=True)
        subprocess.run(
            f"conda activate {self.name}", shell=True, check=True, capture_output=True)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            f"conda remove -n {self.name} --all -y -q", shell=True, capture_output=True, check=True)
