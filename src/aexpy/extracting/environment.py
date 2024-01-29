from abc import abstractmethod
import subprocess
from typing import Callable, override
from aexpy.environments import ExecutionEnvironment, ExecutionEnvironmentRunner
from aexpy.environments.conda import CondaEnvironment, CondaEnvironmentBuilder
from aexpy.extracting import Extractor
from logging import Logger

from aexpy.models import ApiDescription
from aexpy.utils import logProcessResult


def getExtractorEnvironment(name: str, logger: Logger | None = None):
    return CondaEnvironment(name, ["pydantic"], logger=logger)


def getExtractorEnvironmentBuilder(logger: Logger | None = None):
    return CondaEnvironmentBuilder("aex-ext-", ["pydantic"], logger=logger)


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
        runner: ExecutionEnvironmentRunner,
    ):
        """Extract the API description in the environment."""
        pass

    @override
    def extract(self, dist, product):
        with self.env as runner:
            if dist.dependencies:
                for dep in dist.dependencies:
                    try:
                        res = runner.runPythonText(f"-m pip install {dep}")
                        # res = run(f"python -m pip --version", capture_output=True, text=True)
                        logProcessResult(self.logger, res)
                        res.check_returncode()
                    except Exception as ex:
                        self.logger.error(
                            f"Failed to install dependency: {dep}", exc_info=ex
                        )
            self.extractInEnv(product, runner)
