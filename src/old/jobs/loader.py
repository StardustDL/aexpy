import logging
import pathlib
from typing import Iterable, Tuple

from ..analyses.models import ApiCollection
from ..diffs.models import DiffCollection
from ..logging.models import PayloadLog


class AnalysisResultLoader:
    def __init__(self, results: pathlib.Path) -> None:
        self.path = results

    def projects(self) -> Iterable[str]:
        if not (self.path.exists() and self.path.is_dir()):
            raise StopIteration()
        for item in self.path.iterdir():
            yield item.name

    def versions(self, project: str) -> Iterable[str]:
        subdir = self.path.joinpath(project)
        if not (subdir.exists() and subdir.is_dir()):
            raise StopIteration()
        for item in subdir.glob("*.log.json"):
            yield item.stem.replace(".log", "")

    def result(self, project: str, version: str) -> Tuple[ApiCollection | None, PayloadLog] | Exception:
        from ..analyses.serializer import deserialize
        from ..logging.serializer import deserialize as logDeserialize

        try:
            path = self.path.joinpath(project)
            logPath = path.joinpath(f"{version}.log.json")
            resultPath = path.joinpath(f"{version}.json")
            log = logDeserialize(logPath.read_text())
            result = deserialize(resultPath.read_text()) if resultPath.exists(
            ) and resultPath.is_file() else None
            return result, log
        except Exception as ex:
            logging.error(
                f"Failed to load analysis {project} @ {version}", exc_info=ex)
            return ex

    def items(self, project: str | None = None) -> Iterable[Tuple[str, str]]:
        if project is None:
            for proj in self.projects():
                for ver in self.versions(proj):
                    yield proj, ver
        else:
            for ver in self.versions(project):
                yield project, ver

    def results(self, project: str | None = None) -> Iterable[Tuple[str, str, Tuple[ApiCollection | None, PayloadLog] | Exception]]:
        for proj, ver in self.items(project):
            yield proj, ver, self.result(proj, ver)


class DiffResultLoader:
    def __init__(self, results: pathlib.Path) -> None:
        self.path = results

    def items(self) -> Iterable[str]:
        if not (self.path.exists() and self.path.is_dir()):
            raise StopIteration()
        for item in self.path.glob("*.json"):
            yield item.stem

    def result(self, id: str) -> DiffCollection | None | Exception:
        from ..diffs.serializer import deserialize

        try:
            resultPath = self.path.joinpath(f"{id}.json")
            result = deserialize(resultPath.read_text()) if resultPath.exists(
            ) and resultPath.is_file() else None
            return result
        except Exception as ex:
            logging.error(f"Failed to load diff {id}", exc_info=ex)
            return ex

    def results(self) -> Iterable[Tuple[str, DiffCollection | None | Exception]]:
        for id in self.items():
            yield id, self.result(id)
