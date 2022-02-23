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

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, generator: "ReportGenerator | None" = None, fileSuffix: "str" = "txt") -> None:
        super().__init__(logger, cache, options)
        from .text import TextReportGenerator
        self.generator = generator or TextReportGenerator()

        self.fileSuffix = fileSuffix
        """The file suffix for the generated report."""

    def getOutFile(self, oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking") -> "Path | None":
        return super().getOutFile(oldRelease, newRelease, oldDistribution, newDistribution, oldDescription, newDescription, diff, bc).with_suffix(f".{self.fileSuffix}")

    def process(self, product: "Report", oldRelease: "Release", newRelease: "Release", oldDistribution: "Distribution", newDistribution: "Distribution", oldDescription: "ApiDescription", newDescription: "ApiDescription", diff: "ApiDifference", bc: "ApiBreaking"):
        data = ProcessData(oldRelease, newRelease, oldDistribution,
                           newDistribution, oldDescription, newDescription, diff, bc)
        if product.file:
            ensureDirectory(product.file.parent)
            with product.file.open("w") as out:
                self.generator.generate(data, out)
        else:
            self.logger.warning(
                "No file to output report to. Skipping.")
