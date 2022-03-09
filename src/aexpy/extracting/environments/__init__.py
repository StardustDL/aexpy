import subprocess
from abc import abstractmethod
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import json
from aexpy.environments import ExecutionEnvironment
from aexpy.models import ApiDescription, Distribution
from aexpy.producer import ProducerOptions

from .. import DefaultExtractor, Extractor


class EnvirontmentExtractor(DefaultExtractor):
    """Extractor in a environment."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, env: "ExecutionEnvironment | None" = None) -> None:
        super().__init__(logger, cache, options)
        from .default import DefaultEnvironment
        self.env = env or DefaultEnvironment

    @abstractmethod
    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess]"):
        """Extract the API description in the environment."""

        pass

    def process(self, product: "ApiDescription", dist: "Distribution"):
        with self.env(dist.pyversion) as run:
            res = run(
                f"python -m pip install {dist.wheelFile}", capture_output=True, text=True)
            # res = run(f"python -m pip --version", capture_output=True, text=True)
            self.logger.info(
                f"Install wheel: {dist.wheelFile} with exit code {res.returncode}")
            if res.stdout.strip():
                self.logger.debug(f"STDOUT:\n{res.stdout}")
            if res.stderr.strip():
                self.logger.info(f"STDERR:\n{res.stderr}")
            res.check_returncode()
            self.extractInEnv(product, run)
