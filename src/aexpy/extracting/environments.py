from abc import abstractmethod
from logging import Logger
from pathlib import Path
import subprocess
import json
from typing import Callable
from uuid import uuid1

from aexpy.models import ApiDescription, Distribution
from . import Extractor


class ExtractorEnvironment:
    def __init__(self, pythonVersion: str = "3.7") -> None:
        self.pythonVersion = pythonVersion

    def run(self, command: str, **kwargs):
        return subprocess.run(command, **kwargs)

    def __enter__(self):
        return self.run

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class CondaEnvironment(ExtractorEnvironment):
    baseEnv: "dict[str, str]" = {}

    @classmethod
    def clearBase(cls):
        cls.reloadBase()
        for key, item in list(cls.baseEnv.items()):
            subprocess.run(
                f"conda remove -n {item} --all -y -q", shell=True, check=True, capture_output=True)
            del cls.baseEnv[key]

    @classmethod
    def reloadBase(cls):
        envs = json.loads(subprocess.run("conda env list --json", shell=True,
                          capture_output=True, text=True, check=True).stdout)["envs"]
        envs = [Path(item).name for item in envs]
        for item in envs:
            if item.startswith("aexpy-extbase-"):
                cls.baseEnv[item.removeprefix("aexpy-extbase-")] = item

    def __init__(self, pythonVersion: str = "3.7") -> None:
        super().__init__(pythonVersion)
        self.name = f"py{self.pythonVersion}-{uuid1()}"

    def run(self, command: str, **kwargs):
        return subprocess.run(f"conda activate {self.name} && {command}", **kwargs, shell=True)

    def __enter__(self):
        if not self.baseEnv:
            self.reloadBase()
        if self.pythonVersion not in self.baseEnv:
            baseName = f"aexpy-extbase-{self.pythonVersion}"
            subprocess.run(
                f"conda create -n {baseName} python={self.pythonVersion} -y -q", shell=True, check=True, capture_output=True)
            subprocess.run(
                f"conda activate {baseName} && python -m pip install mypy", shell=True, check=True, capture_output=True)
            self.baseEnv[self.pythonVersion] = baseName
        subprocess.run(
            f"conda create -n {self.name} --clone {self.baseEnv[self.pythonVersion]} -y -q", shell=True, check=True, capture_output=True)
        subprocess.run(
            f"conda activate {self.name}", shell=True, check=True, capture_output=True)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            f"conda remove -n {self.name} --all -y -q", shell=True, capture_output=True, check=True)


class EnvirontmentExtractor(Extractor):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, env: "ExtractorEnvironment | None" = None) -> None:
        super().__init__(logger, cache, redo)
        self.env = env or CondaEnvironment

    @abstractmethod
    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess]"):
        pass

    def extract(self, dist: "Distribution") -> "ApiDescription":
        cacheFile = self.cache / dist.release.project / \
            f"{dist.release.version}.json"

        with ApiDescription(distribution=dist).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None:
                with self.env(dist.pyversion) as run:
                    res = run(
                        f"python -m pip install {dist.wheelFile}", capture_output=True, text=True)
                    self.logger.info(
                        f"Install wheel: {dist.wheelFile} with exit code {res.returncode}")
                    if res.stdout.strip():
                        self.logger.debug(f"STDOUT:\n{res.stdout}")
                    if res.stderr.strip():
                        self.logger.info(f"STDERR:\n{res.stderr}")
                    res.check_returncode()
                    self.extractInEnv(ret, run)

        return ret
