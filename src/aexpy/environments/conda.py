import json
import platform
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
    if platform.system() == "Linux":
        envs: list[str] = json.loads(
            subprocess.run(
                "conda env list --json",
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )["envs"]
        envs.sort(key=lambda x: len(x))
        return f". {envs[0]}/etc/profile.d/conda.sh && "
    return ""


class CondaEnvironment(ExecutionEnvironment):
    """Conda environment."""

    def __init__(
        self,
        /,
        name: str,
        packages: list[str] | None = None,
        logger: Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self.name = name
        self.packages = packages or []
        """Required packages in the environment."""

    @override
    def runner(self, /):
        return ExecutionEnvironmentRunner(
            commandPrefix=f"{getCommandPre()}conda activate {self.name} &&",
            pythonName="python",
        )

    def __enter__(self, /):
        self.logger.debug(f"Activate conda env: {self.name}")
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


class CondaEnvironmentBuilder(ExecutionEnvironmentBuilder[CondaEnvironment]):
    """Conda environment builder."""

    def __init__(
        self,
        /,
        envprefix: str = "conda-aex-",
        packages: list[str] | None = None,
        logger: Logger | None = None,
    ) -> None:
        super().__init__(logger=logger)

        self.envprefix = envprefix
        """Created environment name prefix."""

        self.packages = packages or []
        """Required packages in the environment."""

    @override
    def build(self, /, pyversion="3.12", logger=None):
        name = f"{self.envprefix}{pyversion}-{uuid1()}"
        res = subprocess.run(
            f"conda create -n {name} python={pyversion} -c conda-forge -y -q",
            shell=True,
            capture_output=True,
            text=True,
        )
        logProcessResult(self.logger, res)
        res.check_returncode()
        res = subprocess.run(
            f"{getCommandPre()}conda activate {name} && python -m pip install {f' '.join(self.packages)}",
            shell=True,
            capture_output=True,
            text=True,
        )
        logProcessResult(self.logger, res)
        res.check_returncode()
        return CondaEnvironment(name=name, logger=logger)

    @override
    def clean(self, /, env):
        subprocess.run(
            f"conda remove -n {env.name} --all -y -q",
            shell=True,
            capture_output=True,
            check=True,
        )
