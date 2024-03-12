import logging
import subprocess
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import override


class ExecutionEnvironmentRunner:
    def __init__(
        self, /, commandPrefix: str = "", pythonName: str = "python", **options
    ) -> None:
        self.commandPrefix = commandPrefix
        self.pythonName = pythonName
        self.options = options

    def run(self, /, command: str, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the environment."""

        return subprocess.run(
            f"{self.commandPrefix} {command}".strip(),
            **kwargs,
            **self.options,
            shell=True,
        )

    def runPython(self, /, command: str, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the environment."""

        return subprocess.run(
            f"{self.commandPrefix} {self.pythonName} {command}".strip(),
            **kwargs,
            **self.options,
            shell=True,
        )

    def runText(self, /, command: str, **kwargs) -> subprocess.CompletedProcess[str]:
        """Run a command in the environment."""

        return subprocess.run(
            f"{self.commandPrefix} {command}".strip(),
            **kwargs,
            **self.options,
            capture_output=True,
            text=True,
            shell=True,
        )

    def runPythonText(
        self, /, command: str, **kwargs
    ) -> subprocess.CompletedProcess[str]:
        """Run a command in the environment."""

        return subprocess.run(
            f"{self.commandPrefix} {self.pythonName} {command}".strip(),
            **kwargs,
            **self.options,
            capture_output=True,
            text=True,
            shell=True,
        )


class ExecutionEnvironment:
    """Environment that runs extractor code."""

    def __init__(self, /, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("exe-env")
        """Python version of the environment."""

    def runner(self, /):
        return ExecutionEnvironmentRunner()

    def __enter__(self, /):
        self.logger.debug(f"Enter the environment: {self=}")
        return self.runner()

    def __exit__(self, /, exc_type, exc_val, exc_tb):
        self.logger.debug(f"Exit the environment: {self=}")


class ExecutionEnvironmentBuilder[T: ExecutionEnvironment](ABC):
    """Builder to create environment that runs extractor code."""

    def __init__(self, /, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("exe-env-builder")

    @abstractmethod
    def build(
        self, /, pyversion: str = "3.12", logger: logging.Logger | None = None
    ) -> T: ...

    @abstractmethod
    def clean(self, /, env: T): ...

    @contextmanager
    def use(self, /, pyversion: str = "3.12", logger: logging.Logger | None = None):
        logger = logger or self.logger.getChild("sub-env")
        self.logger.debug(f"Build env {pyversion=}")
        try:
            env = self.build(pyversion=pyversion, logger=logger)
        except Exception:
            self.logger.error(f"Failed to create env {pyversion=}", exc_info=True)
            raise
        self.logger.info(f"Built env {pyversion=}, {env=}")

        self.logger.debug(f"Use env {pyversion=}, {env=}")
        try:
            yield env
        except Exception:
            self.logger.error(f"Error occurs when using env {env=}", exc_info=True)
            raise
        finally:
            self.logger.info(f"Used env {pyversion=}, {env=}")
            self.logger.debug(f"Clean env {pyversion=}, {env=}")
            try:
                self.clean(env)
            except Exception:
                self.logger.error(
                    f"Failed to clean env {pyversion=}, {env=}", exc_info=True
                )
                raise
            self.logger.info(f"Cleaned env {pyversion=}, {env=}")


class CurrentEnvironment(ExecutionEnvironment):
    """Use the same environment for extractor."""

    @override
    def runner(self, /):
        return ExecutionEnvironmentRunner(pythonName=sys.executable)


class SingleExecutionEnvironmentBuilder[T: ExecutionEnvironment](
    ExecutionEnvironmentBuilder[T]
):
    def __init__(self, /, env: T, logger: logging.Logger | None = None) -> None:
        super().__init__(logger=logger or env.logger)
        self.env = env

    @override
    def build(self, /, pyversion="3.12", logger=None):
        return self.env

    @override
    def clean(self, /, env: T):
        pass
