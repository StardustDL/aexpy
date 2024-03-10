import gzip
import logging
import os
import subprocess
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import override

import aexpy
from aexpy.models import (ApiDescription, ApiDifference, Distribution, Product,
                          Report)


@dataclass
class AexPyResult[T: Product]:
    code: int
    log: bytes
    out: bytes
    data: T | None = None

    def ensure(self, /):
        assert self.code == 0, f"Failed with exitcode {self.code}"
        return self

    def save(self, /, path: Path):
        path.write_bytes(self.out)
        (path.with_suffix(".log")).write_bytes(self.log)


class AexPyWorker:
    def __init__(
        self,
        /,
        verbose: int = 0,
        compress: bool = False,
        cwd: Path | None = None,
        logger: Logger | None = None,
    ) -> None:
        self.verbose = min(5, max(0, verbose))
        self.compress = compress
        self.logger = logger or logging.getLogger()
        self.cwd = cwd or Path(os.getcwd()).resolve()

    def getCommandPrefix(self, /):
        return ["aexpy"]

    def resolvePath(self, /, path: Path):
        return path

    def run(self, /, args: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            self.getCommandPrefix()
            + (["-" + "v" * self.verbose] if self.verbose > 0 else [])
            + args,
            capture_output=True,
            env={
                **os.environ,
                "PYTHONUTF8": "1",
                "AEXPY_GZIP_IO": "1" if self.compress else "0",
                "AEXPY_ENV_PROVIDER": aexpy.getEnvironmentManager(),
            },
            cwd=self.cwd,
            **kwargs,
        )

    def runParsedOutput[T: Product](self, /, type: type[T], args: list[str], **kwargs):
        res = self.run(args + ["-"], **kwargs)
        result = AexPyResult[T](code=res.returncode, log=res.stderr, out=res.stdout)
        try:
            if self.compress:
                result.data = type.model_validate_json(gzip.decompress(result.out))
            else:
                result.data = type.model_validate_json(result.out)
        except Exception:
            self.logger.error("Failed to parse aexpy output", exc_info=True)
            result.data = None
        return result

    def preprocessParse(self, /, args: list[str], **kwargs):
        return self.runParsedOutput(Distribution, ["preprocess"] + args, **kwargs)

    def extract(self, /, args: list[str], **kwargs):
        return self.runParsedOutput(ApiDescription, ["extract"] + args, **kwargs)

    def diff(self, /, args: list[str], **kwargs):
        return self.runParsedOutput(ApiDifference, ["diff"] + args, **kwargs)

    def report(self, /, args: list[str], **kwargs):
        return self.runParsedOutput(Report, ["report"] + args, **kwargs)

    def version(self, /):
        return (
            self.run(["--version"], check=True)
            .stdout.decode()
            .strip()
            .removeprefix("aexpy v")
            .removesuffix(".")
        )


class AexPyDockerWorker(AexPyWorker):
    @classmethod
    def defaultTag(cls):
        return f"stardustdl/aexpy:v{aexpy.__version__}"

    def __init__(
        self,
        /,
        verbose: int = 0,
        compress: bool = False,
        cwd: Path | None = None,
        logger: Logger | None = None,
        *,
        tag: str = "",
    ) -> None:
        super().__init__(verbose, compress, cwd, logger)
        self.tag = tag or self.defaultTag()

    def getImageTag(self, /, version: str):
        return f"stardustdl/aexpy:v{version}"

    @override
    def getCommandPrefix(self, /):
        return [
            "docker",
            "run",
            "-i",
            "-v",
            f"{str(self.cwd.resolve())}:/data",
            "-u",
            "root",
            "--rm",
            self.tag,
        ] + (["--gzip"] if self.compress else [])

    @override
    def resolvePath(self, /, path):
        return Path("/data/").joinpath(path.relative_to(self.cwd))
