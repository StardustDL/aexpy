from abc import abstractmethod
from logging import Logger
from pathlib import Path
import subprocess
import json
from typing import Callable
from uuid import uuid1

from aexpy.models import ApiDescription, Distribution
from aexpy.producer import ProducerOptions
from .. import Extractor


class ExtractorEnvironment:
    def __init__(self, pythonVersion: str = "3.7") -> None:
        self.pythonVersion = pythonVersion

    def run(self, command: str, **kwargs):
        return subprocess.run(command, **kwargs)

    def __enter__(self):
        return self.run

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class EnvirontmentExtractor(Extractor):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, env: "ExtractorEnvironment | None" = None) -> None:
        super().__init__(logger, cache, options)
        from .default import DefaultEnvironment
        self.env = env or DefaultEnvironment

    @abstractmethod
    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess]"):
        pass

    def extract(self, dist: "Distribution") -> "ApiDescription":
        cacheFile = self.cache / dist.release.project / \
            f"{dist.release.version}.json" if self.cached else None

        with ApiDescription(distribution=dist).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None:
                with self.env(dist.pyversion) as run:
                    res = run(
                        f"python -m pip install {dist.wheelFile}", capture_output=True, text=True)
                    self.logger.info(
                        f"Install wheel: {dist.wheelFile} with exit code {res.returncode}")
                    if res.stdout.strip():
                        self.logger.debug(f"STDOUT:\n{res.stdout}")
                    if res.stderr.strip():
                        self.logger.info(f"STDERR:\n{res.stderr}")
                    res.check_returncode()
                    self.extractInEnv(ret, run)

        return ret
