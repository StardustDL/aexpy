import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Callable

from . import releases

from aexpy.models import Product, Release

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProjectItem:
    project: "str"
    index: "int"
    total: "int"
    func: "Callable[[Release], Product]"


@dataclass
class VersionItem:
    project: "ProjectItem"
    index: "int"
    total: "int"
    release: "Release"


def _processVersion(version: VersionItem):
    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.release.version} ({version.index}/{version.total}).")

        count = 5
        while count > 0:
            count -= 1
            try:
                print(f"    Processing {version.release}.")

                res = version.project.func(version.release)

                assert res.success, f"Processing {version.release} failed."

                print(f"    Processed {version.release}.")

                count = 0
            except Exception as ex:
                print(
                    f"Error for {version.release}: {ex}, retrying")
    except Exception as ex:
        print(f"Error for {version.release}: {ex}")


def _processProject(project: ProjectItem):
    try:
        print(
            f"Process {project.project} ({project.index}/{project.total}).")
        rels = releases.getReleases(project.project)
        totalVersion = len(rels)
        items = []
        for versionIndex, item in enumerate(rels):
            items.append(VersionItem(
                project, versionIndex + 1, totalVersion, item))

        with ProcessPoolExecutor() as pool:
            pool.map(_processVersion, items)
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")


class SingleProcessor:
    def __init__(self, processor: "Callable[[Release], Product]") -> None:
        self.processor = processor

    def processVersion(self, project: str, version: str):
        _processVersion(VersionItem(ProjectItem(
            project, 1, 1, self.processor), 1, 1, Release(project, version)))

    def processProject(self, project: str):
        _processProject(ProjectItem(project, 1, 1, self.processor))

    def processProjects(self, projects: list[str]):
        items = []
        for projectIndex, item in enumerate(projects):
            items.append(ProjectItem(item, projectIndex +
                         1, len(projects), self.processor))

        with ProcessPoolExecutor() as pool:
            pool.map(_processProject, items)
