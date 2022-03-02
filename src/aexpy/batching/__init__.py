import subprocess
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from logging import Logger
from pathlib import Path
from types import ModuleType

from aexpy import getAppDirectory, getCacheDirectory
from aexpy.env import getPipeline
from aexpy.models import Product, ProjectResult, Release, ReleasePair
from aexpy.producer import DefaultProducer, Producer, ProducerOptions


class Batcher(Producer):
    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "batching"

    @abstractmethod
    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "ProjectResult":
        """Batch process a project."""

        pass


class DefaultBatcher(Batcher, DefaultProducer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, provider: "str | None" = None) -> None:
        super().__init__(logger, cache, options)
        from aexpy.env import env
        self.provider = provider or env.provider

    def getProduct(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "ProjectResult":
        return ProjectResult(project=project, pipeline=self.provider)

    def getCacheFile(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "Path | None":
        return self.cache / self.provider / f"{project}.json"

    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 3):
        pass

    def batch(self, project: "str", workers: "int | None" = None, retry: "int" = 3) -> "ProjectResult":
        return self.produce(project=project)


class InProcessBatcher(DefaultBatcher):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, provider: "str | None" = None, stages: "ModuleType | None" = None) -> None:
        super().__init__(logger, cache, options, provider)
        from . import stages as defaultStages
        self.stages = stages or defaultStages

    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 3):
        from .generators import (pair, single)
        from .processor import Processor

        count: "dict[str, int]" = {}

        self.logger.info(f"JOB: Processing {project} @ {datetime.now()}.")

        singles: "list[Release]" = single(project)
        product.releases = singles

        count["preprocess"] = len(singles)
        self.logger.info(
            f"JOB: Preprocess {project}: {len(singles)} releases @ {datetime.now()}.")
        success, failed = Processor(self.stages.pre, self.logger).process(
            singles, workers=workers, retry=retry, stage="Preprocess", provider=self.provider)
        self.logger.info(
            f"JOB: Preprocessed {project}: {len(success)}/{len(singles)} @ {datetime.now()}.")
        product.preprocessed = success
        count["preprocessed"] = len(success)

        singles = success
        count["extract"] = len(singles)
        self.logger.info(f"JOB: Extract {project}: {len(singles)} releases.")
        success, failed = Processor(self.stages.ext, self.logger).process(
            singles, workers=workers, retry=retry, stage="Extract", provider=self.provider)
        self.logger.info(
            f"JOB: Extracted {project}: {len(success)}/{len(singles)} @ {datetime.now()}.")

        product.extracted = success
        count["extracted"] = len(success)

        singles = success
        pairs = pair(singles)
        product.pairs = pairs

        count["diff"] = len(pairs)
        self.logger.info(
            f"JOB: Diff {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, failed = Processor(self.stages.dif, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Diff", provider=self.provider)
        self.logger.info(
            f"JOB: Diffed {project}: {len(success)}/{len(pairs)} @ {datetime.now()}.")
        product.diffed = success
        count["diffed"] = len(success)

        pairs = success
        count["evaluate"] = len(pairs)
        self.logger.info(
            f"JOB: Evaluate {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, failed = Processor(self.stages.eva, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Evaluate", provider=self.provider)
        self.logger.info(
            f"JOB: Evaluated {project}: {len(success)}/{len(pairs)} @ {datetime.now()}.")

        product.evaluated = success
        count["evaluated"] = len(success)

        pairs = success
        count["report"] = len(pairs)
        self.logger.info(
            f"JOB: Report {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, failed = Processor(self.stages.rep, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Report", provider=self.provider)
        self.logger.info(
            f"JOB: Reported {project}: {len(success)}/{len(pairs)} @ {datetime.now()}.")
        product.reported = success
        count["reported"] = len(success)

        pairs = success
        self.logger.info(
            f"JOB: Finish {project}: {len(pairs)} pairs @ {datetime.now()}.")

        self.logger.info(
            f"JOB: Summary {project} @ {datetime.now()}: {', '.join((f'{k}: {v}' for k,v in count.items()))}.")


def getDefault() -> "Batcher":
    return InProcessBatcher()
