import code
from logging import Logger
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
    def stage(self):
        return "pidiff-eval"

    def eval(self, diff: "ApiDifference") -> "ApiBreaking":
        cacheFile = self.cache / "results" / diff.old.release.project / \
            f"{diff.old.release}&{diff.new.release}.json"

        with ApiBreaking(old=diff.old, new=diff.new).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None:
                pyver = diff.old.pyversion

                res = subprocess.run(["docker", "run", "--rm", f"pidiff:{pyver}", f"{diff.old.release.project}=={diff.old.release.version}",
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


class Reporter(Base):
    def stage(self):
        return "pidiff-report"

    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        from aexpy.reporting.default import Reporter
        return Reporter(self.logger, self.cache, self.redo).report(oldRelease, newRelease, oldDistribution, newDistribution, oldDescription, newDescription, diff, bc)


def getPipeline():
    return EmptyPipeline(evaluator=Evaluator(),
                         preprocessor=getDefault(),
                         reporter=Reporter())
