import platform
import subprocess
from abc import abstractmethod
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import json
from aexpy.models import ApiDescription, Distribution
from aexpy.utils import getObjectId

from . import ExecutionEnvironment


class CondaEnvironment(ExecutionEnvironment):
    """Conda environment."""

    __baseenvprefix__ = "conda-aexbase-"
    """Base environment name prefix."""

    __envprefix__ = "conda-aex-"
    """Created environment name prefix."""

    __packages__ = []
    """Required packages in the environment."""

    @classmethod
    def _getCommandPre(cls):
        if not hasattr(cls, "__commandprefix__"):
            if platform.system() == "Linux":
                envs: "list[str]" = json.loads(subprocess.run("conda env list --json", shell=True,
                                                              capture_output=True, text=True, check=True).stdout)["envs"]
                envs.sort(key=lambda x: len(x))
                cls.__commandprefix__ = f". {envs[0]}/etc/profile.d/conda.sh && "
            else:
                cls.__commandprefix__ = ""
        return cls.__commandprefix__

    @classmethod
    def buildAllBase(cls):
        """Build all base environments."""
        this = getObjectId(cls)
        print(f"Building all conda base environments of {this}...")
        bases = cls.reloadBase()
        for i in range(7, 11):
            name = f"3.{i}"
            if name not in bases:
                print(f"Building base environment of {this} for {name}...")
                res = cls.buildBase(name)
                print(f"Base environment of {this} for {name} built: {res}.")

    @classmethod
    def buildBase(cls, version: "str") -> "str":
        """Build base environment for given python version."""

        baseName = f"{cls.__baseenvprefix__}{version}"
        subprocess.run(
            f"conda create -n {baseName} python={version} -y -q", shell=True, check=True)
        packages = ["orjson", *cls.__packages__]
        subprocess.run(
            f"{cls._getCommandPre()}conda activate {baseName} && python -m pip install {f' '.join(packages)}", shell=True, check=True)
        return baseName

    @classmethod
    def clearBase(cls):
        """Clear all base environments."""

        this = getObjectId(cls)
        print(f"Clearing conda base environments of {this}.")
        baseEnv = cls.reloadBase()
        for key, item in list(baseEnv.items()):
            print(f"Removing conda env {key} of {this}: {item}.")
            subprocess.run(
                f"conda remove -n {item} --all -y -q", shell=True, check=True)

    @classmethod
    def clearEnv(cls):
        """Clear all created environments."""

        this = getObjectId(cls)
        print(f"Clearing conda created environments of {this}.")
        envs = json.loads(subprocess.run("conda env list --json", shell=True,
                          capture_output=True, text=True, check=True).stdout)["envs"]
        envs = [Path(item).name for item in envs]
        baseEnv: "dict[str,str]" = {}
        for item in envs:
            if item.startswith(cls.__envprefix__):
                baseEnv[item.removeprefix(cls.__envprefix__)] = item
        for key, item in list(baseEnv.items()):
            print(f"Removing conda env {key} of {this}: {item}.")
            subprocess.run(
                f"conda remove -n {item} --all -y -q", shell=True, check=True)

    @classmethod
    def reloadBase(cls):
        """Reload created base environments."""

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
        return subprocess.run(f"{self._getCommandPre()}conda activate {self.name} && {command}", **kwargs, shell=True)

    def __enter__(self):
        if self.pythonVersion not in self.baseEnv:
            self.baseEnv[self.pythonVersion] = self.buildBase(
                self.pythonVersion)
        subprocess.run(
            f"conda create -n {self.name} --clone {self.baseEnv[self.pythonVersion]} -y -q", shell=True, check=True, capture_output=True)
        subprocess.run(
            f"{self._getCommandPre()}conda activate {self.name}", shell=True, check=True, capture_output=True)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            f"conda remove -n {self.name} --all -y -q", shell=True, capture_output=True, check=True)
