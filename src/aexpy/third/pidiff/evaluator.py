import code
import subprocess
from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy import getCacheDirectory
from aexpy.evaluating import DefaultEvaluator
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.preprocessing import getDefault
from aexpy.producer import ProducerOptions

MAPPER = {
    "B110": "RemoveModule",
    "B111": "RemoveExternalModule",
    "N210": "AddModule",
    "N211": "AddExternalModule",
    "B100": "RemoveAttribute",
    "B120": "RemoveFunction",
    "B130": "RemoveMethod",
    "B140": "RemoveClass",
    "N200": "AddAttribute",
    "N220": "AddFunction",
    "N230": "AddMethod",
    "N240": "AddClass",
    "B300": "RemoveParameter",
    "B310": "AddParameter",
    "B320": "MoveParameter",
    "B330": "UnpositionalParameter",
    "B340": "RemoveVarPositional",
    "B350": "RemoveVarKeyword",
    "B800": "Uncallable",
    "N400": "AddOptionalParameter",
    "N410": "AddParameterDefault",
    "N440": "AddVarPositional",
    "N450": "AddVarKeyword",
}


class Evaluator(DefaultEvaluator):
    __baseenvprefix__ = "pidiff-extbase"

    @classmethod
    def buildAllBase(cls):
        print("Building all pidiff base images...")
        bases = cls.reloadBase()
        for i in range(7, 11):
            name = f"3.{i}"
            if name not in bases:
                print(f"Building image for {name}...")
                res = cls.buildBase(name)
                print(f"Image for {name} built: {res}.")

    @classmethod
    def buildBase(cls, version: "str") -> "str":
        from .docker import buildVersion
        return buildVersion(cls.__baseenvprefix__, version)

    @classmethod
    def clearBase(cls):
        print("Clearing pidiff base images.")
        baseEnv = cls.reloadBase()
        for key, item in list(baseEnv.items()):
            print(f"Removing image {key}: {item}.")
            subprocess.run(["docker", "rmi", item], check=True)

    @classmethod
    def reloadBase(cls):
        envs = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                              capture_output=True, text=True, check=True).stdout.strip().splitlines()
        baseEnv: "dict[str, str]" = {}
        for item in envs:
            if item.startswith(cls.__baseenvprefix__):
                baseEnv[item.split(":")[1]] = item
        return baseEnv

    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "pidiff"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.baseEnv: "dict[str, str]" = self.reloadBase()

    def process(self, product: "ApiBreaking", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        pyver = diff.old.pyversion

        if pyver not in self.baseEnv:
            self.baseEnv[pyver] = self.buildBase(pyver)

        modules = list(set(diff.old.topModules) | set(diff.new.topModules))

        failed: "dict[str, int]" = {}

        for item in modules:
            res = subprocess.run(["docker", "run", "--rm", f"{self.__baseenvprefix__}:{pyver}", f"{diff.old.release.project}=={diff.old.release.version}",
                                  f"{diff.new.release.project}=={diff.new.release.version}", item], text=True, capture_output=True)

            self.logger.info(
                f"Inner pidiff for module {item} exit with: {res.returncode}")

            if res.stdout:
                self.logger.info(f"STDOUT for module {item}: {res.stdout}")
            if res.stderr:
                self.logger.error(f"STDERR for module {item}: {res.stderr}")

            if res.returncode not in {0, 30, 99, 88}:
                self.logger.error(
                    f"Inner pidiff for module {item} failed, exit with: {res.returncode}.")
                failed[item] = res.returncode
                continue

            for line in res.stdout.splitlines():
                try:
                    subs = line.split(":", 2)
                    file = subs[0]
                    line = int(subs[1])
                    subs = subs[2].strip().split(" ", 1)
                    type = subs[0]
                    message = subs[1]
                    if type in MAPPER:
                        kind = MAPPER[type]
                    else:
                        kind = type
                    entry = DiffEntry(
                        id=str(uuid1()), kind=kind,
                        rank=BreakingRank.High if type.startswith(
                            "B") else BreakingRank.Compatible,
                        message=f"{kind} @ {file}:{line}: {message}")

                    self.logger.info(f"{line} -> {entry}")

                    product.entries.update({entry.id: entry})
                except Exception as ex:
                    self.logger.warning(
                        f"Error for module {item} parsing line: {line}: {ex}")

        if failed:
            self.logger.error(f"Failed modules: {failed}")

        if modules:
            assert len(failed) < len(modules), "All modules failed."
