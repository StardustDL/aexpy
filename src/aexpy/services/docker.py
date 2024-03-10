from functools import cached_property
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import override

from aexpy.io import StreamProductSaver

from .. import diffing, extracting, preprocessing, reporting
from ..producers import Producer
from ..tools.workers import AexPyDockerWorker, AexPyWorker
from . import ServiceProvider


class WorkerProducer(Producer):
    def __init__(self, /, worker: AexPyWorker):
        super().__init__(worker.logger)
        self.worker = worker


class WorkerDiffer(diffing.Differ, WorkerProducer):
    @override
    def diff(
        self,
        /,
        old: diffing.ApiDescription,
        new: diffing.ApiDescription,
        product: diffing.ApiDifference,
    ):
        with TemporaryDirectory(dir=self.worker.cwd) as tdir:
            temp = Path(tdir).resolve()
            fold = temp / "old.json"
            fnew = temp / "new.json"
            with fold.open("wb") as f:
                StreamProductSaver(f).save(old, "")
            with fnew.open("wb") as f:
                StreamProductSaver(f).save(new, "")
            result = self.worker.diff([str(fold), str(fnew)])
            self.logger.debug(
                f"Internal worker exited with {result.code}, log: {result.log}"
            )
            data = result.ensure().data
            assert data is not None
            product.__init__(**data.model_dump())


class WorkerReporter(reporting.Reporter, WorkerProducer):
    @override
    def report(self, /, diff: diffing.ApiDifference, product: reporting.Report):
        with TemporaryDirectory(dir=self.worker.cwd) as tdir:
            temp = Path(tdir).resolve()
            file = temp / "diff.json"
            with file.open("wb") as f:
                StreamProductSaver(f).save(diff, "")
            result = self.worker.report([str(file)])
            self.logger.debug(
                f"Internal worker exited with {result.code}, log: {result.log}"
            )
            data = result.ensure().data
            assert data is not None
            product.__init__(**data.model_dump())


class DockerServiceProvider(ServiceProvider):
    def __init__(self, volume: Path, tag: str = "") -> None:
        super().__init__(f"image-{tag}")
        self.tag = tag
        self.volume = volume

    def worker(self, logger: Logger | None = None):
        return AexPyDockerWorker(
            tag=self.tag,
            cwd=self.volume,
            verbose=5,
            compress=True,
            logger=logger,
        )

    @override
    def differ(self, /, logger: Logger | None = None) -> diffing.Differ:
        return WorkerDiffer(self.worker(logger=logger))

    @override
    def reporter(self, /, logger: Logger | None = None) -> reporting.Reporter:
        return WorkerReporter(self.worker(logger=logger))
