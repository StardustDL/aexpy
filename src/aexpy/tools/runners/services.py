import os
from logging import Logger
from pathlib import Path
from typing import Callable, override

from ...cli import CliOptions
from ...environments import (CurrentEnvironment, ExecutionEnvironmentBuilder,
                             SingleExecutionEnvironmentBuilder)
from ...services import ServiceProvider
from . import (AexPyDockerRunner, AexPyRunner, RunnerDiffer, RunnerExtractor,
               RunnerReporter)


class RunnerServiceProvider(ServiceProvider):
    def __init__(self, name: str | None = None) -> None:
        super().__init__(name or "runner")

    def runner(self, logger: Logger | None = None):
        def build(path: Path):
            return AexPyRunner(
                cwd=path,
                cli=CliOptions(verbose=5, compress=True),
                logger=logger,
            )

        return build

    @override
    def environmentBuilder(self, /, logger=None):
        return SingleExecutionEnvironmentBuilder(env=CurrentEnvironment(logger=logger))

    @override
    def differ(self, /, logger=None):
        return RunnerDiffer(self.runner(logger=logger), logger=logger)

    @override
    def reporter(self, /, logger=None):
        return RunnerReporter(self.runner(logger=logger), logger=logger)

    @override
    def extractor(self, /, logger=None, env=None):
        return RunnerExtractor(self.runner(logger=logger), logger=logger)


class DockerRunnerServiceProvider(RunnerServiceProvider):
    def __init__(self, tag: str = "", name: str | None = None) -> None:
        super().__init__(name or f"image-{tag}")
        self.tag = tag

    @override
    def runner(self, logger: Logger | None = None):
        def build(path: Path):
            return AexPyDockerRunner(
                tag=self.tag,
                cwd=path,
                cli=CliOptions(verbose=5, compress=True),
                logger=logger,
            )

        return build
