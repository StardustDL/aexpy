import gzip
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, override

from ... import __version__, getEnvironmentManager
from ...cli import CliOptions
from ...diffing import Differ
from ...extracting import Extractor
from ...io import StreamProductSaver
from ...models import (ApiDescription, ApiDifference, Distribution, Product,
                       Report)
from ...producers import Producer
from ...reporting import Reporter


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


class AexPyRunner:
    def __init__(
        self,
        /,
        cwd: Path | None = None,
        cli: CliOptions | None = None,
        logger: Logger | None = None,
    ) -> None:
        self.cli = cli or CliOptions()
        self.logger = logger or logging.getLogger()
        self.cwd = cwd or Path(os.getcwd()).resolve()

    def getCommandPrefix(self, /):
        return ["aexpy"]

    def resolvePath(self, /, path: Path):
        return path

    def run(self, /, args: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        args = self.getCommandPrefix() + self.cli.args() + args
        self.logger.debug(f"Runner run args: {args}")

        kwargs.setdefault("capture_output", True)
        kwargs.setdefault(
            "env",
            {
                **os.environ,
                "PYTHONUTF8": "1",
                "AEXPY_GZIP_IO": "1" if self.cli.compress else "0",
                "AEXPY_ENV_PROVIDER": getEnvironmentManager(),
            },
        )
        kwargs.setdefault("cwd", self.cwd)

        result = subprocess.run(
            args,
            **kwargs,
        )
        self.logger.debug(f"Runner run exited with {result.returncode}")
        return result

    def runParsedOutput[T: Product](self, /, type: type[T], args: list[str], **kwargs):
        res = self.run(args + ["-"], **kwargs)
        result = AexPyResult[T](code=res.returncode, log=res.stderr, out=res.stdout)
        try:
            if self.cli.compress:
                result.data = type.model_validate_json(gzip.decompress(result.out))
            else:
                result.data = type.model_validate_json(result.out)
        except Exception:
            self.logger.error("Failed to parse aexpy output", exc_info=True)
            self.logger.warning(result.out)
            result.data = None
        return result

    def preprocess(self, /, args: list[str | Path], **kwargs):
        return self.runParsedOutput(
            Distribution,
            ["preprocess"]
            + [s if isinstance(s, str) else str(self.resolvePath(s)) for s in args],
            **kwargs,
        )

    def extract(self, /, args: list[str | Path], **kwargs):
        return self.runParsedOutput(
            ApiDescription,
            ["extract"]
            + [s if isinstance(s, str) else str(self.resolvePath(s)) for s in args],
            **kwargs,
        )

    def diff(self, /, args: list[str | Path], **kwargs):
        return self.runParsedOutput(
            ApiDifference,
            ["diff"]
            + [s if isinstance(s, str) else str(self.resolvePath(s)) for s in args],
            **kwargs,
        )

    def report(self, /, args: list[str | Path], **kwargs):
        return self.runParsedOutput(
            Report,
            ["report"]
            + [s if isinstance(s, str) else str(self.resolvePath(s)) for s in args],
            **kwargs,
        )

    def version(self, /):
        return (
            self.run(["--version"], check=True)
            .stdout.decode()
            .strip()
            .split(", ", maxsplit=1)[0]
            .removeprefix("aexpy v")
        )


class AexPyDockerRunner(AexPyRunner):
    @classmethod
    def defaultTag(cls):
        return f"stardustdl/aexpy:v{__version__}"

    def __init__(
        self,
        /,
        cwd: Path | None = None,
        cli: CliOptions | None = None,
        logger: Logger | None = None,
        *,
        tag: str = "",
    ) -> None:
        super().__init__(cwd, cli, logger)
        self.tag = tag or self.defaultTag()

    def getImageTag(self, /, version: str):
        return f"stardustdl/aexpy:v{version}"

    @override
    def getCommandPrefix(self, /):
        user = "root"

        try:
            import pwd

            uid = os.getuid()  # type: ignore
            gid = pwd.getpwuid(uid).pw_gid  # type: ignore
            user = f"{uid}:{gid}"
        except Exception:
            pass

        return (
            [
                "docker",
                "run",
                "-i",
                "-v",
                f"{str(self.cwd.resolve())}:/data",
                "-u",
                user,
                "--rm",
            ]
            + (["-t"] if self.cli.interact else [])
            + [self.tag]
        )

    @override
    def resolvePath(self, /, path):
        return Path("/data/").joinpath(path.relative_to(self.cwd))


class RunnerProducer(Producer):
    def __init__(
        self, /, runner: Callable[[Path], AexPyRunner], logger: Logger | None = None
    ):
        super().__init__(logger)
        self.runner = runner


class RunnerDiffer(Differ, RunnerProducer):
    @override
    def diff(
        self,
        /,
        old: ApiDescription,
        new: ApiDescription,
        product: ApiDifference,
    ):
        with TemporaryDirectory() as tdir:
            temp = Path(tdir).resolve()
            runner = self.runner(temp)

            fold = temp / "old.json"
            fnew = temp / "new.json"
            with fold.open("wb") as f:
                StreamProductSaver(f).save(old, "")
            with fnew.open("wb") as f:
                StreamProductSaver(f).save(new, "")

            result = runner.diff([fold, fnew])
            self.logger.debug(f"Internal runner exited with {result.code}")
            self.logger.debug("Inner log: " + result.log.decode())
            data = result.ensure().data
            assert data is not None
            product.__init__(**data.model_dump())


class RunnerReporter(Reporter, RunnerProducer):
    @override
    def report(self, /, diff: ApiDifference, product: Report):
        with TemporaryDirectory() as tdir:
            temp = Path(tdir).resolve()
            runner = self.runner(temp)

            file = temp / "diff.json"
            with file.open("wb") as f:
                StreamProductSaver(f).save(diff, "")

            result = runner.report([file])
            self.logger.debug(f"Internal runner exited with {result.code}")
            self.logger.debug("Inner log: " + result.log.decode())
            data = result.ensure().data
            assert data is not None
            product.__init__(**data.model_dump())


def cloneDistribution(dist: Distribution, target: Path):
    assert (
        dist.rootPath and dist.rootPath.is_dir()
    ), "Distribution root file not exists."
    src = target / "src"
    assert not src.exists(), f"Target subdirectory exists: {src}."
    shutil.copytree(dist.rootPath, src)
    result = dist.model_copy(update={"rootPath": src})
    if dist.wheelFile:
        wheel = target / dist.wheelFile.name
        shutil.copy(dist.wheelFile, wheel)
        result.wheelFile = wheel
    return result


class RunnerExtractor(Extractor, RunnerProducer):
    @override
    def extract(self, /, dist, product):
        with TemporaryDirectory() as tdir:
            temp = Path(tdir).resolve()
            runner = self.runner(temp)
            cloned = cloneDistribution(dist, temp)
            if cloned.rootPath:
                cloned.rootPath = runner.resolvePath(cloned.rootPath)
            if cloned.wheelFile:
                cloned.wheelFile = runner.resolvePath(cloned.wheelFile)

            file = temp / "dist.json"
            with file.open("wb") as f:
                StreamProductSaver(f).save(cloned, "")

            result = runner.extract([file, "--temp"])
            self.logger.debug(
                f"Internal runner exited with {result.code}\n{result.log.decode()}"
            )
            data = result.ensure().data
            assert data is not None
            product.__init__(**data.model_dump())
