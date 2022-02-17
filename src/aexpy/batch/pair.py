import functools
import random
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import sleep
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
    parallel: "bool"


@dataclass
class VersionItem:
    project: "ProjectItem"
    index: "int"
    total: "int"
    old: "Release"
    new: "Release"


def _processVersion(version: "VersionItem") -> "bool":
    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.old.version} & {version.new.version} ({version.index}/{version.total}).")

        count = 3
        while count > 0:
            count -= 1
            try:
                print(f"    Processing {version.old} & {version.new}.")

                res = version.project.func(version.old, version.new)
                assert res.success, "Result is not successful"

                print(f"    Processed {version.old} & {version.new}.")
                return True
            except Exception as ex:
                print(
                    f"    Error for {version.old} & {version.new}: {ex}, retrying")
                sleep(random.random())
    except Exception as ex:
        print(
            f"  Error for {version.old} & {version.new}: {ex}")

    print(f"  Failed to process {version.old} & {version.new}.")
    return False


def compareVersion(a, b):
    a = pkgVersion.parse(a)
    b = pkgVersion.parse(b)
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0


def _processProject(project: ProjectItem) -> "list[tuple[Release, Release, bool]]":
    ret = []
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
                f"  Failed to sort versions by packaging.version {project.project}: {versions} Exception: {ex}")
            try:
                versions.sort(key=functools.cmp_to_key(semver.compare))
            except Exception as ex:
                versions = [r.version for r in rels]
                print(
                    f"  Failed to sort versions by semver {project.project}: {versions} Exception: {ex}")

        from aexpy.pipelines import Pipeline
        pipeline = Pipeline()

        for version in versions:
            rel = Release(project.project, version)
            dist = pipeline.preprocess(rel)
            if dist.success:
                downloadedVersion.append(rel)
        if len(downloadedVersion) <= 1:
            print(
                f"  No enough download version for {project.project} ({project.index}/{project.total}).")
            return

        items: "list[VersionItem]" = []
        lastVersion: "Release | None" = None
        total = len(downloadedVersion) - 1
        for versionIndex, item in enumerate(downloadedVersion):
            if lastVersion is None:
                pass
            else:
                items.append(VersionItem(project, versionIndex +
                             1, total, lastVersion, item))
            lastVersion = item

        with ProcessPoolExecutor(max_workers=None if project.parallel else 1) as pool:
            results = list(pool.map(_processVersion, items))

        ret = [(items[i].old, items[i].new, results[i])
               for i in range(len(results))]
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")

    success = sum((1 for i in results if i))
    failed = ', '.join(
        (f'{i[0].version}&{i[1].version}' for i in ret if not i[2]))
    print(
        f"Processed {len(ret)} pairs for {project.project} (Success: {success}, Failed: {failed or '0'}).")
    return ret


class PairProcessor:
    def __init__(self, processor: "Callable[[Release, Release], Product]") -> None:
        self.processor = processor

    def processVersion(self, project: str, old: str, new: str):
        _processVersion(VersionItem(ProjectItem(project, 1, 1, self.processor),
                        1, 1, Release(project, old), Release(project, new)))

    def processProject(self, project: "str", parallel: "bool" = True):
        _processProject(ProjectItem(project, 1, 1, self.processor, parallel))

    def processProjects(self, projects: "list[str]", parallel: "bool" = True, parallelVersion: "bool" = True):
        items = []
        for projectIndex, item in enumerate(projects):
            items.append(ProjectItem(item, projectIndex +
                         1, len(projects), self.processor, parallelVersion))

        with ProcessPoolExecutor(max_workers=None if parallel else 1) as pool:
            results = list(pool.map(_processProject, items))

        print(f"Processed {len(results)} projects: {projects}.")
        for i in range(len(results)):
            print(
                f"  {projects[i]}: {sum((1 for b in results[i] if b[2]))}/{len(results[i])}")