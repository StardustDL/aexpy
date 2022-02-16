import functools
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Callable
import semver
from packaging import version as pkgVersion

from aexpy.pipelines import Pipeline

from . import releases

from aexpy.models import Product, Release

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProjectItem:
    project: "str"
    index: "int"
    total: "int"
    func: "Callable[[Release, Release], Product]"


@dataclass
class VersionItem:
    project: "ProjectItem"
    index: "int"
    total: "int"
    old: "Release"
    new: "Release"


def _processVersion(version: VersionItem):
    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.old.version} & {version.new.version} ({version.index}/{version.total}).")

        count = 3
        while count > 0:
            count -= 1
            try:
                print(f"    Processing {version.old} & {version.new}.")

                res = version.project.func(version.old, version.new)

                assert res.success, f"Processing {version.old} & {version.new} failed."

                print(f"    Processed {version.old} & {version.new}.")

                count = 0
            except Exception as ex:
                print(
                    f"Error for {version.project.project} @ {version.old.version} & {version.new.version}: {ex}, retrying")
    except Exception as ex:
        print(
            f"Error for {version.project.project} @ {version.old.version} & {version.new.version}: {ex}")


def compareVersion(a, b):
    a = pkgVersion.parse(a)
    b = pkgVersion.parse(b)
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0


def _processProject(project: ProjectItem):
    try:
        print(
            f"Process {project.project} ({project.index}/{project.total}).")
        rels = releases.getReleases(project.project)

        downloadedVersion: "list[Release]" = []
        versions = [r.version for r in rels]
        try:
            versions.sort(key=functools.cmp_to_key(compareVersion))
        except Exception as ex:
            versions = [r.version for r in rels]
            print(
                f"Failed to sort versions by packaging.version {project.project}: {versions} Exception: {ex}")
            try:
                versions.sort(key=functools.cmp_to_key(semver.compare))
            except Exception as ex:
                versions = [r.version for r in rels]
                print(
                    f"Failed to sort versions by semver {project.project}: {versions} Exception: {ex}")

        from aexpy.pipelines import Pipeline
        pipeline = Pipeline()

        for version in versions:
            rel = Release(project.project, version)
            dist = pipeline.preprocess(rel)
            if dist.success:
                downloadedVersion.append(rel)
        if len(downloadedVersion) <= 1:
            print(
                f"No enough download version for {project.project} ({project.index}/{project.total}).")
            return

        items = []
        lastVersion: "Release | None" = None
        total = len(downloadedVersion) - 1
        for versionIndex, item in enumerate(downloadedVersion):
            if lastVersion is None:
                pass
            else:
                items.append(VersionItem(project, versionIndex +
                             1, total, lastVersion, item))
            lastVersion = item

        with ProcessPoolExecutor() as pool:
            pool.map(_processVersion, items)
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")


class PairProcessor:
    def __init__(self, processor: "Callable[[Release, Release], Product]") -> None:
        self.processor = processor

    def processVersion(self, project: str, old: str, new: str):
        _processVersion(VersionItem(ProjectItem(project, 1, 1, self.processor),
                        1, 1, Release(project, old), Release(project, new)))

    def processProject(self, project: str):
        _processProject(ProjectItem(project, 1, 1, self.processor))

    def processProjects(self, projects: list[str]):
        items = []
        for projectIndex, item in enumerate(projects):
            items.append(ProjectItem(item, projectIndex +
                         1, len(projects), self.processor))

        with ProcessPoolExecutor() as pool:
            pool.map(_processProject, items)
