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
    def prepare(cls):
        for i in range(7, 11):
            cls.buildBase(f"3.{i}")

    @classmethod
    def buildBase(cls, version: "str") -> None:
        from .docker import buildVersion
        return buildVersion(cls.__baseenvprefix__, version)

    def clearBase(self):
        self.reloadBase()
        for key, item in list(self.baseEnv.items()):
            subprocess.run(f"docker rmi {item}",
                           check=True, capture_output=True)
            del self.baseEnv[key]

    def reloadBase(self):
        envs = subprocess.run("docker images --format '{{.Repository}}:{{.Tag}}'",
                              capture_output=True, text=True, check=True).stdout.strip().splitlines()
        for item in envs:
            if item.startswith(self.__baseenvprefix__):
                self.baseEnv[item.split(":")[1]] = item

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, cached: "bool" = True) -> None:
        super().__init__(logger, cache or getCacheDirectory() /
                         "pidiff" / self.stage(), redo, cached)
        self.baseEnv: "dict[str, str]" = {}

    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        pyver = diff.old.pyversion

        if not self.baseEnv:
            self.reloadBase()
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
