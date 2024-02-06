from logging import Logger
import platform
import subprocess
from pathlib import Path
from typing import override
from uuid import uuid1
import json
from functools import cache

from aexpy.utils import getObjectId, logProcessResult

from . import (
    ExecutionEnvironment,
    ExecutionEnvironmentBuilder,
    ExecutionEnvironmentRunner,
)


@cache
def getCommandPre():
    return ""


class MambaEnvironment(ExecutionEnvironment):
    """Mamba environment."""
    __mamba_name__ = "micromamba"

    def __init__(
        self, name: str, packages: list[str] | None = None, logger: Logger | None = None
    ) -> None:
        super().__init__(logger)
        self.name = name
        self.packages = packages or []
        """Required packages in the environment."""

    @override
    def runner(self):
        return ExecutionEnvironmentRunner(
            commandPrefix=f"{getCommandPre()}{self.__mamba_name__} activate {self.name} &&",
            pythonName="python",
        )

    def __enter__(self):
        self.logger.info(f"Activate mamba env: {self.name}")
        runner = self.runner()
        if self.packages:
            res = runner.runPythonText(
                f"-m pip install {f' '.join(self.packages)}",
            )
            logProcessResult(self.logger, res)
            res.check_returncode()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MambaEnvironmentBuilder(ExecutionEnvironmentBuilder[MambaEnvironment]):
    """Mamba environment builder."""

    def __init__(
        self,
        envprefix: str = "mamba-aex-",
        packages: list[str] | None = None,
        logger: Logger | None = None,
    ) -> None:
        super().__init__(logger=logger)

        self.envprefix = envprefix
        """Created environment name prefix."""

        self.packages = packages or []
        """Required packages in the environment."""

    @override
    def build(self, pyversion="3.12", logger=None):
        name = f"{self.envprefix}{pyversion}-{uuid1()}"
        res = subprocess.run(
            f"{MambaEnvironment.__mamba_name__} create -n {name} python={pyversion} -c conda-forge -y -q",
            shell=True,
            capture_output=True,
            text=True,
        )
        logProcessResult(self.logger, res)
        res.check_returncode()
        res = subprocess.run(
            f"{getCommandPre()}{MambaEnvironment.__mamba_name__} activate {name} && python -m pip install {f' '.join(self.packages)}",
            shell=True,
            capture_output=True,
            text=True,
        )
        logProcessResult(self.logger, res)
        res.check_returncode()
        return MambaEnvironment(name=name, logger=logger)

    @override
    def clean(self, env):
        subprocess.run(
            f"{MambaEnvironment.__mamba_name__} remove -n {env.name} --all -y -q",
            shell=True,
            capture_output=True,
            check=True,
        )
