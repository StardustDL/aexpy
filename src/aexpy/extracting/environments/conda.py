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

    @classmethod
    def buildAllBase(cls):
        bases = cls.reloadBase()
        for i in range(7, 11):
            name = f"3.{i}"
            if name not in bases:
                cls.buildBase(name)

    @classmethod
    def buildBase(cls, version: "str") -> "str":
        baseName = f"{cls.__baseenvprefix__}{version}"
        subprocess.run(
            f"conda create -n {baseName} python={version} -y -q", shell=True, check=True, capture_output=True)
        if cls.__packages__:
            subprocess.run(
                f"conda activate {baseName} && python -m pip install {f' '.join(cls.__packages__)}", shell=True, check=True, capture_output=True)
        return baseName

    @classmethod
    def clearBase(cls):
        print("Clearing conda base environment.")
        baseEnv = cls.reloadBase()
        for key, item in list(baseEnv.items()):
            print(f"Removing conda env {key}: {item}.")
            subprocess.run(
                f"conda remove -n {item} --all -y -q", shell=True, check=True, capture_output=True)

    @classmethod
    def reloadBase(cls):
        envs = json.loads(subprocess.run("conda env list --json", shell=True,
                          capture_output=True, text=True, check=True).stdout)["envs"]
        envs = [Path(item).name for item in envs]
        baseEnv: "dict[str,str]" = {}
        for item in envs:
            if item.startswith(cls.__baseenvprefix__):
                baseEnv[item.removeprefix(cls.__baseenvprefix__)] = item
        return baseEnv

    def __init__(self, pythonVersion: str = "3.7") -> None:
        super().__init__(pythonVersion)
        self.name = f"{self.__envprefix__}{self.pythonVersion}-{uuid1()}"
        self.baseEnv: "dict[str, str]" = self.reloadBase()

    def run(self, command: str, **kwargs):
        return subprocess.run(f"conda activate {self.name} && {command}", **kwargs, shell=True)

    def __enter__(self):
        if self.pythonVersion not in self.baseEnv:
            self.baseEnv[self.pythonVersion] = self.buildBase(
                self.pythonVersion)
        subprocess.run(
            f"conda create -n {self.name} --clone {self.baseEnv[self.pythonVersion]} -y -q", shell=True, check=True, capture_output=True)
        subprocess.run(
            f"conda activate {self.name}", shell=True, check=True, capture_output=True)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            f"conda remove -n {self.name} --all -y -q", shell=True, capture_output=True, check=True)
