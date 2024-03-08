import subprocess
from functools import cache
from logging import Logger
from typing import override
from uuid import uuid1

from ..utils import logProcessResult
from . import (ExecutionEnvironment, ExecutionEnvironmentBuilder,
               ExecutionEnvironmentRunner)


@cache
def getCommandPre():
    return ""


class MambaEnvironment(ExecutionEnvironment):
    """Mamba environment."""

    def __init__(
        self,
        /,
        name: str,
        packages: list[str] | None = None,
        mamba="micromamba",
        logger: Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self.name = name
        self.packages = packages or []
        """Required packages in the environment."""
        self.mamba = mamba
        """Mamba executable name."""

    @override
    def runner(self, /):
        return ExecutionEnvironmentRunner(
            commandPrefix=f"{getCommandPre()}{self.mamba} run -n {self.name}",
            pythonName="python",
        )

    def __enter__(self, /):
        self.logger.debug(f"Activate mamba env: {self.name}")
        runner = self.runner()
        if self.packages:
            res = runner.runPythonText(
                f"-m pip install {f' '.join(self.packages)}",
            )
            logProcessResult(self.logger, res)
            res.check_returncode()
        return super().__enter__()

    def __exit__(self, /, exc_type, exc_val, exc_tb):
        pass


class MambaEnvironmentBuilder(ExecutionEnvironmentBuilder[MambaEnvironment]):
    """Mamba environment builder."""

    def __init__(
        self,
        /,
        envprefix: str = "mamba-aex-",
        packages: list[str] | None = None,
        mamba="micromamba",
        logger: Logger | None = None,
    ) -> None:
        super().__init__(logger=logger)

        self.envprefix = envprefix
        """Created environment name prefix."""

        self.packages = packages or []
        """Required packages in the environment."""

        self.mamba = mamba
        """Mamba executable name."""

    @override
    def build(self, /, pyversion="3.12", logger=None):
        name = f"{self.envprefix}{pyversion}-{uuid1()}"
        res = subprocess.run(
            f"{self.mamba} create -n {name} python={pyversion} -c conda-forge -y -q",
            shell=True,
            capture_output=True,
            text=True,
        )
        logProcessResult(self.logger, res)
        res.check_returncode()
        res = subprocess.run(
            f"{getCommandPre()}{self.mamba} run -n {name} python -m pip install {f' '.join(self.packages)}",
            shell=True,
            capture_output=True,
            text=True,
        )
        logProcessResult(self.logger, res)
        res.check_returncode()
        return MambaEnvironment(name=name, mamba=self.mamba, logger=logger)

    @override
    def clean(self, /, env):
        subprocess.run(
            f"{self.mamba} remove -n {env.name} --all -y -q",
            shell=True,
            capture_output=True,
            check=True,
        )
