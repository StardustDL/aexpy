import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from logging import Logger
from pathlib import Path
from typing import IO

from aexpy.models import (ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.producers import ProducerOptions
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


class ReportGenerator:
    """Base class for report generators."""

    def generate(self, data: "ProcessData") -> "str":
        """Generate the report."""
        return ""


class GeneratorReporter(Reporter):
    """A reporter that generates reports using a generator."""

    def __init__(self, logger: "Logger | None" = None, generator: "ReportGenerator | None" = None) -> None:
        super().__init__(logger)
        from .text import TextReportGenerator
        self.generator = generator or TextReportGenerator()

    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference", product: "Report"):
        data = ProcessData(oldRelease, newRelease, oldDistribution,
                           newDistribution, oldDescription, newDescription, diff)
        product.content = self.generator.generate(data)
