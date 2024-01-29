from abc import abstractmethod
import subprocess
from typing import Callable, override
from aexpy.environments import ExecutionEnvironment
from aexpy.environments.conda import CondaEnvironment
from aexpy.extracting import Extractor
from logging import Logger

from aexpy.models import ApiDescription


class ExtractorEnvironment(CondaEnvironment):
    """Environment for default extractor."""

    __packages__ = ["pydantic"]


class EnvirontmentExtractor(Extractor):
    """Extractor in a environment."""

    def __init__(
        self, logger: Logger | None = None, env: ExecutionEnvironment | None = None
    ) -> None:
        super().__init__(logger)

        from ..environments import CurrentEnvironment
        self.env = env or CurrentEnvironment(logger)

    @abstractmethod
    def extractInEnv(
        self,
        result: ApiDescription,
        run: Callable[..., subprocess.CompletedProcess],
        runPython: Callable[..., subprocess.CompletedProcess],
    ):
        """Extract the API description in the environment."""
        pass

    @override
    def extract(self, dist, product):
        with self.env as (run, runPython):
            if dist.dependencies:
                for dep in dist.dependencies:
                    try:
                        res = runPython(
                            f"-m pip install {' '.join(dist.dependencies)}",
                            capture_output=True,
                            text=True,
                        )
                        # res = run(f"python -m pip --version", capture_output=True, text=True)
                        self.logger.info(
                            f"Install dependency: '{dep}' with exit code {res.returncode}"
                        )
                        if res.stdout.strip():
                            self.logger.debug(f"STDOUT:\n{res.stdout}")
                        if res.stderr.strip():
                            self.logger.info(f"STDERR:\n{res.stderr}")
                        res.check_returncode()
                    except Exception as ex:
                        self.logger.error(f"Failed to install dependency: {dep}", exc_info=ex)
            self.extractInEnv(product, run, runPython)
