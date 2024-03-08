from abc import abstractmethod
from logging import Logger
from typing import override

from .. import getEnvironmentManager
from ..environments import ExecutionEnvironment, ExecutionEnvironmentRunner
from ..models import ApiDescription
from ..utils import logProcessResult
from . import Extractor


def getExtractorEnvironment(name: str, logger: Logger | None = None):
    env = getEnvironmentManager()
    if env == "conda":
        from ..environments.conda import CondaEnvironment

        return CondaEnvironment(name, ["pydantic"], logger=logger)
    elif env == "mamba":
        from ..environments.mamba import MambaEnvironment

        return MambaEnvironment(name, ["pydantic"], mamba="mamba", logger=logger)
    from ..environments.mamba import MambaEnvironment

    return MambaEnvironment(name, ["pydantic"], logger=logger)


def getExtractorEnvironmentBuilder(logger: Logger | None = None):
    env = getEnvironmentManager()
    if env == "conda":
        from ..environments.conda import CondaEnvironmentBuilder

        return CondaEnvironmentBuilder("aex-ext-", ["pydantic"], logger=logger)
    elif env == "mamba":
        from ..environments.mamba import MambaEnvironmentBuilder

        return MambaEnvironmentBuilder(
            "aex-ext-", ["pydantic"], mamba="mamba", logger=logger
        )
    from ..environments.mamba import MambaEnvironmentBuilder

    return MambaEnvironmentBuilder("aex-ext-", ["pydantic"], logger=logger)


class EnvirontmentExtractor(Extractor):
    """Extractor in a environment."""

    def __init__(
        self, /, logger: Logger | None = None, env: ExecutionEnvironment | None = None
    ) -> None:
        super().__init__(logger)

        from ..environments import CurrentEnvironment

        self.env = env or CurrentEnvironment(logger)

    @abstractmethod
    def extractInEnv(
        self,
        /,
        result: ApiDescription,
        runner: ExecutionEnvironmentRunner,
    ):
        """Extract the API description in the environment."""
        ...

    @override
    def extract(self, /, dist, product):
        with self.env as runner:
            doneDeps = False
            if dist.wheelFile:
                if dist.wheelFile.is_file():
                    self.logger.info(f"Install package wheel file: {dist.wheelFile}")
                    try:
                        res = runner.runPythonText(
                            f"-m pip install {str(dist.wheelFile)}"
                        )
                        logProcessResult(self.logger, res)
                        res.check_returncode()
                        doneDeps = True
                    except Exception:
                        self.logger.error(
                            f"Failed to install wheel file: {dist.wheelFile}",
                            exc_info=True,
                        )
            if not doneDeps and dist.dependencies:
                for dep in dist.dependencies:
                    try:
                        res = runner.runPythonText(f"-m pip install {dep}")
                        # res = run(f"python -m pip --version", capture_output=True, text=True)
                        logProcessResult(self.logger, res)
                        res.check_returncode()
                    except Exception:
                        self.logger.error(
                            f"Failed to install dependency: {dep}", exc_info=True
                        )
            self.extractInEnv(product, runner)
