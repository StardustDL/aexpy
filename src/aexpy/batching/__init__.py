import subprocess
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from logging import Logger
from pathlib import Path
from types import ModuleType

from aexpy import getAppDirectory
from aexpy.env import getPipeline
from aexpy.models import BatchRequest, Product, BatchResult, Release, ReleasePair
from aexpy.producers import DefaultProducer, Producer, ProducerOptions


class Batcher(Producer):
    def batch(self, request: "BatchRequest", product: "BatchResult"):
        """Batch process a project."""
        pass


class InProcessBatcher(Batcher):
    def __init__(self, logger: "Logger | None" = None) -> None:
        super().__init__(logger)

    def batch(self, request: "BatchRequest", product: "BatchResult"):
        project, workers, retry = request.project, request.workers, request.retry

        from . import stages as stages
        if request.index:
            from .stages import loader
            stages = loader

        from .generators import pair, single
        from .processor import Processor

        count: "dict[str, int]" = {}

        self.logger.info(f"JOB: Processing {project} @ {datetime.now()}.")

        singles: "list[Release]" = single(project)
        product.releases = singles

        count["preprocess"] = len(singles)
        self.logger.info(
            f"JOB: Preprocess {project}: {len(singles)} releases @ {datetime.now()}.")
        success, failed = Processor(stages.pre, self.logger).process(
            singles, workers=workers, retry=retry, stage="Preprocess", provider=self.provider)
        self.logger.info(
            f"JOB: Preprocessed {project}: {len(success)}/{len(singles)} @ {datetime.now()}.")
        product.preprocessed = success
        count["preprocessed"] = len(success)

        singles = success
        count["extract"] = len(singles)
        self.logger.info(f"JOB: Extract {project}: {len(singles)} releases.")
        success, failed = Processor(stages.ext, self.logger).process(
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
        success, failed = Processor(stages.dif, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Diff", provider=self.provider)
        self.logger.info(
            f"JOB: Diffed {project}: {len(success)}/{len(pairs)} @ {datetime.now()}.")
        product.differed = success
        count["differed"] = len(success)

        pairs = success
        count["evaluate"] = len(pairs)
        self.logger.info(
            f"JOB: Evaluate {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, failed = Processor(stages.eva, self.logger).process(
            pairs, workers=workers, retry=retry, stage="Evaluate", provider=self.provider)
        self.logger.info(
            f"JOB: Evaluated {project}: {len(success)}/{len(pairs)} @ {datetime.now()}.")

        product.evaluated = success
        count["evaluated"] = len(success)

        pairs = success
        count["report"] = len(pairs)
        self.logger.info(
            f"JOB: Report {project}: {len(pairs)} pairs @ {datetime.now()}.")
        success, failed = Processor(stages.rep, self.logger).process(
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
    
