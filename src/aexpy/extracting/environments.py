from pathlib import Path
import subprocess
import json
from uuid import uuid1


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
                f"conda remove -n {item} --all -y", shell=True, check=True)
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
                f"conda create -n {baseName} python={self.pythonVersion} -y", shell=True, check=True)
            subprocess.run(f"conda activate {baseName} && python -m pip install mypy", shell=True, check=True)
            self.baseEnv[self.pythonVersion] = baseName
        subprocess.run(
            f"conda create -n {self.name} --clone {self.baseEnv[self.pythonVersion]} -y", shell=True, check=True)
        subprocess.run(
            f"conda activate {self.name}", shell=True, check=True)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.check_call(
            f"conda remove -n {self.name} --all -y", shell=True)
