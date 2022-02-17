from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from logging import Logger
from pathlib import Path
import sys
from typing import IO

from aexpy.models import ApiDescription, Distribution, Release, ApiBreaking, ApiDifference, Report
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.reporting import Reporter
from aexpy.utils import TeeFile, ensureDirectory


@dataclass
class ProcessData:
    oldRelease: "Release"
    newRelease: "Release"
    oldDistribution: "Distribution"
    newDistribution: "Distribution"
    oldDescription: "ApiDescription"
    newDescription: "ApiDescription"
    diff: "ApiDifference"
    bc: "ApiBreaking"


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, data: "ProcessData", file: "IO[str]"):
        pass


class GeneratorReporter(Reporter):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, redo: "bool" = False, cached: "bool" = True, generator: "ReportGenerator | None" = None, fileSuffix: "str" = "txt", stdout: "bool" = True) -> None:
        super().__init__(logger, cache, redo, cached)
        from .text import TextReportGenerator
        self.generator = generator or TextReportGenerator()
        self.fileSuffix = fileSuffix
        self.stdout = stdout

    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        assert oldDistribution.release == oldRelease, f"{oldDistribution.release} != {oldRelease}"
        assert newDistribution.release == newRelease, f"{newDistribution.release} != {newRelease}"
        assert oldDescription.distribution.release == oldRelease, f"{oldDescription.distribution.release} != {oldRelease}"
        assert newDescription.distribution.release == newRelease, f"{newDescription.distribution.release} != {newRelease}"
        assert diff.old.release == oldRelease, f"{diff.old.release} != {oldRelease}"
        assert diff.new.release == newRelease, f"{diff.new.release} != {newRelease}"
        assert bc.old.release == oldRelease, f"{bc.old.release} != {oldRelease}"
        assert bc.new.release == newRelease, f"{bc.new.release} != {newRelease}"

        cacheFile = self.cache / "results" / oldRelease.project / \
            f"{oldRelease}&{newRelease}.json" if self.cached else None
        outFile = self.cache / "reports" / oldRelease.project / \
            f"{oldRelease}&{newRelease}.{self.fileSuffix}" if self.cached else None

        with Report(old=oldRelease, new=newRelease, file=outFile).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None or not ret.file or not ret.file.exists():
                data = ProcessData(oldRelease, newRelease, oldDistribution,
                                   newDistribution, oldDescription, newDescription, diff, bc)
                if ret.file:
                    ensureDirectory(ret.file.parent)
                    with ret.file.open("w") as out:
                        file = TeeFile(out, sys.stdout) if self.stdout else out
                        self.generator.generate(data, file)
                else:
                    if self.stdout:
                        self.generator.generate(data, sys.stdout)
                    else:
                        self.logger.warning(
                            "Stdout is disabled and no file was provided")
            else:
                if self.stdout:
                    print(ret.file.read_text(), file=sys.stdout)

        return ret
