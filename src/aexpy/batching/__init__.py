import subprocess
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from logging import Logger
from pathlib import Path

from aexpy import getAppDirectory, getCacheDirectory
from aexpy.env import getPipeline
from aexpy.models import Product, Release
from aexpy.producer import DefaultProducer, Producer, ProducerOptions


@dataclass
class ProjectResult(Product):
    """
    A result of a batch run.
    """
    project: "str" = ""
    pipeline: "str" = ""
    count: "dict[str, int]" = field(default_factory=dict)

    def load(self, data: "dict"):
        super().load(data)
        if "project" in data and data["project"] is not None:
            self.project = data.pop("project")
        if "pipeline" in data and data["pipeline"] is not None:
            self.pipeline = data.pop("pipeline")
        if "count" in data and data["count"] is not None:
            self.count = data.pop("count")

    def overview(self) -> "str":
        from aexpy.reporting.generators.text import StageIcons
        counts = []
        for item in StageIcons:
            if item in self.count:
                ed = item.rstrip("e") + "ed"
                c = self.count[item]
                ced = self.count.get(ed, 0)
                counts.append(
                    f"  {StageIcons[item]} {item.capitalize()} {ced}/{c} ({ced / c * 100:.2f}%)")
        countstr = '\n'.join(counts)
        return super().overview().replace("overview", f"{self.project}") + f"""
  🧰 {self.pipeline}
{countstr}"""


class Batcher(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "batching"

    @abstractmethod
    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "ProjectResult":
        """Batch process a project."""

        pass


class DefaultBatcher(Batcher, DefaultProducer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.pipeline = None

    def getProduct(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "ProjectResult":
        if self.pipeline is None:
            self.pipeline = getPipeline()
        return ProjectResult(project=project, pipeline=self.pipeline.name)

    def getCacheFile(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "Path | None":
        if self.pipeline is None:
            self.pipeline = getPipeline()
        return self.cache / self.pipeline.name / f"{project}.json"

    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 3):
        pass

    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "ProjectResult":
        return self.produce(project=project)


class InProcessBatcher(DefaultBatcher):
    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 3):
        from . import stages
        from .generators import (diffed, evaluated, extracted, pair,
                                 preprocessed, reported, single)
        from .processor import Processor

        if self.pipeline is None:
            self.pipeline = getPipeline()

        self.logger.info(f"JOB: Processing {project} @ {datetime.now()}.")

        singles: "list[Release]" = single(project)
        product.count["preprocess"] = len(singles)
        self.logger.info(
            f"JOB: Preprocess {project}: {len(singles)} releases @ {datetime.now()}.")
        success, total = Processor(stages.pre, self.logger).process(
            singles, workers=workers, retry=retry, stage="Preprocess")
        self.logger.info(
            f"JOB: Preprocessed {project}: {success}/{total} @ {datetime.now()}.")

        singles = list(filter(preprocessed(self.pipeline), singles))
        product.count["preprocessed"] = len(singles)
        product.count["extract"] = len(singles)
        self.logger.info(f"JOB: Extract {project}: {len(singles)} releases.")
        success, total = Processor(stages.ext, self.logger).process(
            singles, workers=workers, retry=retry, stage="Extract")
        self.logger.info(
            f"JOB: Extracted {project}: {success}/{total} @ {datetime.now()}.")

        singles = list(filter(extracted(self.pipeline), singles))
        product.count["extracted"] = len(singles)
        pairs = pair(singles)
        product.count["diff"] = len(pairs)
        self.logger.info(
            f"JOB: Diff {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, total = Processor(stages.dif, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Diff")
        self.logger.info(
            f"JOB: Diffed {project}: {success}/{total} @ {datetime.now()}.")

        pairs = list(filter(diffed(self.pipeline), pairs))
        product.count["diffed"] = len(pairs)
        product.count["evaluate"] = len(pairs)
        self.logger.info(
            f"JOB: Evaluate {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, total = Processor(stages.eva, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Evaluate")
        self.logger.info(
            f"JOB: Evaluated {project}: {success}/{total} @ {datetime.now()}.")

        pairs = list(filter(evaluated(self.pipeline), pairs))
        product.count["evaluated"] = len(pairs)
        product.count["report"] = len(pairs)
        self.logger.info(
            f"JOB: Report {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, total = Processor(stages.rep, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Report")
        self.logger.info(
            f"JOB: Reported {project}: {success}/{total} @ {datetime.now()}.")

        pairs = list(filter(reported(self.pipeline), pairs))
        product.count["reported"] = len(pairs)
        self.logger.info(
            f"JOB: Finish {project}: {len(pairs)} pairs @ {datetime.now()}.")

        self.logger.info(
            f"JOB: Summary {project} @ {datetime.now()}: {', '.join((f'{k}: {v}' for k,v in product.count.items()))}.")


def getDefault() -> "Batcher":
    return InProcessBatcher()
