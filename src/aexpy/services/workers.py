import os
from logging import Logger
from pathlib import Path
from typing import Callable, override

from ..environments import (CurrentEnvironment, ExecutionEnvironmentBuilder,
                            SingleExecutionEnvironmentBuilder)
from ..models import ApiDescription, Distribution
from ..producers import ProduceContext
from ..tools.workers import (AexPyDockerWorker, AexPyWorker, WorkerDiffer,
                             WorkerExtractor, WorkerReporter)
from . import ServiceProvider


class WorkerServiceProvider(ServiceProvider):
    def __init__(self, name: str | None = None) -> None:
        super().__init__(name or "worker")

    def worker(self, logger: Logger | None = None):
        def build(path: Path):
            return AexPyWorker(
                cwd=path,
                verbose=5,
                compress=True,
                logger=logger,
            )

        return build

    @override
    def environmentBuilder(self, /, logger=None):
        return SingleExecutionEnvironmentBuilder(env=CurrentEnvironment(logger=logger))

    @override
    def differ(self, /, logger=None):
        return WorkerDiffer(self.worker(logger=logger), logger=logger)

    @override
    def reporter(self, /, logger=None):
        return WorkerReporter(self.worker(logger=logger), logger=logger)

    @override
    def extractor(self, /, logger=None, env=None):
        return WorkerExtractor(self.worker(logger=logger), logger=logger)


class DockerWorkerServiceProvider(WorkerServiceProvider):
    def __init__(self, tag: str = "", name: str | None = None) -> None:
        super().__init__(name or f"image-{tag}")
        self.tag = tag

    @override
    def worker(self, logger: Logger | None = None):
        def build(path: Path):
            return AexPyDockerWorker(
                tag=self.tag,
                cwd=path,
                verbose=5,
                compress=True,
                logger=logger,
            )

        return build

    @override
    def extract(self, /, dist, *, logger=None, context=None, envBuilder=None):
        result = super().extract(
            dist, logger=logger, context=context, envBuilder=envBuilder
        )
        if hasattr(os, "getuid"):
            if getattr(os, "getuid")() != 0:
                result.logger.warning(
                    "Not running in root, tempfile created by the inner container might not be able to cleaned."
                )
        return result
