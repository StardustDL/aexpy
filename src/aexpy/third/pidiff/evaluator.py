import code
from logging import Logger
from aexpy import getCacheDirectory
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.reporting import Reporter as Base

from pathlib import Path
import subprocess
from uuid import uuid1
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.preprocessing import getDefault
from aexpy.evaluating import Evaluator as Base
from aexpy.models import ApiBreaking, ApiDifference, Release
from aexpy.pipelines import EmptyPipeline


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
    "N210": "AddFunction",
    "N220": "AddMethod",
    "N230": "AddClass",
    "B300": "RemoveParameter",
    "B310": "AddParameter",
    "B320": "ReorderParameter",
    "B330": "UnpositionalParameter",
    "B340": "RemoveVarPositional",
    "B350": "RemoveVarKeyword",
    "B800": "Uncallable",
    "N400": "AddOptionalParameter",
    "N410": "AddParameterDefault",
    "N440": "AddVarPositional",
    "N450": "AddVarKeyword",
}


class Evaluator(Base):
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
    def buildBase(cls, version: "str") -> None:
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

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, cached: "bool" = True) -> None:
        super().__init__(logger, cache or getCacheDirectory() /
                         "pidiff" / "evaluating", redo, cached)
        self.baseEnv: "dict[str, str]" = self.reloadBase()

    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        pyver = diff.old.pyversion

        if pyver not in self.baseEnv:
            self.baseEnv[pyver] = self.buildBase(pyver)

        cacheFile = self.cache / "results" / diff.old.release.project / \
            f"{diff.old.release}&{diff.new.release}.json" if self.cached else None

        with ApiBreaking(old=diff.old, new=diff.new).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None:
                res = subprocess.run(["docker", "run", "--rm", f"{self.__baseenvprefix__}:{pyver}", f"{diff.old.release.project}=={diff.old.release.version}",
                                      f"{diff.new.release.project}=={diff.new.release.version}"], text=True, capture_output=True)

                if res.stdout:
                    self.logger.info(f"STDOUT: {res.stdout}")
                if res.stderr:
                    self.logger.error(f"STDERR: {res.stderr}")

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
                        entry = DiffEntry(str(uuid1()), kind, BreakingRank.High if type.startswith(
                            "B") else BreakingRank.Compatible, f"{kind} @ {file}:{line}: {message}")

                        self.logger.info(f"{line} -> {entry}")

                        ret.entries.update({entry.id: entry})
                    except Exception as e:
                        self.logger.warning(f"Error parsing line: {line}")

        return ret
