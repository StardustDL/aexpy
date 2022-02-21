from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from logging import Logger
from pathlib import Path
import subprocess
from aexpy import getCacheDirectory, getAppDirectory
from aexpy.env import getPipeline

from aexpy.models import Product, Release
from aexpy.producer import DefaultProducer, Producer, ProducerOptions


@dataclass
class ProjectResult(Product):
    """
    A result of a batch run.
    """
    project: "str" = ""
    count: "dict[str, int]" = field(default_factory=dict)

    def load(self, data: "dict"):
        super().load(data)
        if "project" in data and data["project"] is not None:
            self.release = data.pop("project")
        if "count" in data and data["count"] is not None:
            self.count = data.pop("count")

    def overview(self) -> "str":
        countstr = '\n'.join(f"    {k}: {v}" for k, v in self.count.items())
        return f"""Project Result: {self.project}
{countstr}"""


class Batcher(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "batching"

    @abstractmethod
    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 5) -> "ProjectResult":
        """Batch process a project."""

        pass


class DefaultBatcher(Batcher, DefaultProducer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.pipeline = None

    def getProduct(self, project: "str", workers: "int | None" = None, retry: "int" = 5) -> "ProjectResult":
        return ProjectResult(project=project)

    def getCacheFile(self, project: "str", workers: "int | None" = None, retry: "int" = 5) -> "Path | None":
        if self.pipeline is None:
            self.pipeline = getPipeline()
        return self.cache / self.pipeline.name / f"{project}.json"

    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 5):
        pass

    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 5) -> "ProjectResult":
        return self.produce(project=project)


class InProcessBatcher(DefaultBatcher):
    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 5):
        from .generators import single, pair, preprocessed, extracted, diffed, evaluated, reported
        from .processor import Processor
        from . import default

        if self.pipeline is None:
            self.pipeline = getPipeline()

        self.logger.info(f"JOB: Processing {project} @ {datetime.now()}.")

        singles: "list[Release]" = single(project)
        product.count["preprocess"] = len(singles)
        self.logger.info(
            f"JOB: Preprocess {project}: {len(singles)} releases @ {datetime.now()}.")
        Processor(default.pre, self.logger).process(
            singles, workers=workers, retry=retry, stage="Preprocess")

        singles = list(filter(preprocessed(self.pipeline), singles))
        product.count["preprocessed"] = len(singles)
        product.count["extract"] = len(singles)
        self.logger.info(f"JOB: Extract {project}: {len(singles)} releases.")
        Processor(default.ext, self.logger).process(
            singles, workers=workers, retry=retry, stage="Extract")

        singles = list(filter(extracted(self.pipeline), singles))
        product.count["extracted"] = len(singles)
        pairs = pair(singles)
        product.count["diff"] = len(pairs)
        self.logger.info(
            f"JOB: Diff {project}: {len(pairs)} pairs @ {datetime.now()}.")
        Processor(default.dif, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Diff")

        pairs = list(filter(diffed(self.pipeline), pairs))
        product.count["diffed"] = len(pairs)
        product.count["evaluate"] = len(pairs)
        self.logger.info(
            f"JOB: Evaluate {project}: {len(pairs)} pairs @ {datetime.now()}.")
        Processor(default.eva, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Evaluate")

        pairs = list(filter(evaluated(self.pipeline), pairs))
        product.count["evaluated"] = len(pairs)
        product.count["report"] = len(pairs)
        self.logger.info(
            f"JOB: Report {project}: {len(pairs)} pairs @ {datetime.now()}.")
        Processor(default.rep, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Report")

        pairs = list(filter(reported(self.pipeline), pairs))
        product.count["reported"] = len(pairs)
        self.logger.info(
            f"JOB: Finish {project}: {len(pairs)} pairs @ {datetime.now()}.")

        self.logger.info(
            f"JOB: Summary {project} @ {datetime.now()}: {', '.join((f'{k}: {v}' for k,v in product.count.items()))}.")


def getDefault() -> "Batcher":
    return InProcessBatcher()
