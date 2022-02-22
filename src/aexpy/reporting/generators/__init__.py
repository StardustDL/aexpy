import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from logging import Logger
from pathlib import Path
from typing import IO

from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.producer import ProducerOptions
from aexpy.reporting import DefaultReporter
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
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, data: "ProcessData", file: "IO[str]"):
        """Generate the report."""

        pass


class GeneratorReporter(DefaultReporter):
    """A reporter that generates reports using a generator."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, generator: "ReportGenerator | None" = None, fileSuffix: "str" = "txt", stdout: "bool" = True) -> None:
        super().__init__(logger, cache, options)
        from .text import TextReportGenerator
        self.generator = generator or TextReportGenerator()

        self.fileSuffix = fileSuffix
        """The file suffix for the generated report."""

        self.stdout = stdout
        """Whether to write the report to stdout."""

    def getOutFile(self, oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking") -> "Path | None":
        return super().getOutFile(oldRelease, newRelease, oldDistribution, newDistribution, oldDescription, newDescription, diff, bc).with_suffix(f".{self.fileSuffix}")

    def process(self, product: "Report", oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking"):
        data = ProcessData(oldRelease, newRelease, oldDistribution,
                           newDistribution, oldDescription, newDescription, diff, bc)
        if product.file:
            ensureDirectory(product.file.parent)
            with product.file.open("w") as out:
                file = TeeFile(out, sys.stdout) if self.stdout else out
                self.generator.generate(data, file)
        else:
            if self.stdout:
                self.generator.generate(data, sys.stdout)
            else:
                self.logger.warning(
                    "Stdout is disabled and no file was provided")

    def onCached(self, product: "Report", oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking"):
        if self.stdout:
            if product.file and product.file.exists():
                print(product.file.read_text(), file=sys.stdout)
            else:
                self.process(product, oldRelease, newRelease, oldDistribution,
                             newDistribution, oldDescription, newDescription, diff, bc)
