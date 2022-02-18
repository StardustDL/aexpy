import random
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import sleep
from typing import Callable

from . import releases
from ..env import Options, env

from aexpy.models import Product, Release

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProjectItem:
    project: "str"
    index: "int"
    total: "int"
    func: "Callable[[Release, bool], Product]"
    parallel: "bool"
    options: "Options"


@dataclass
class VersionItem:
    project: "ProjectItem"
    index: "int"
    total: "int"
    release: "Release"


def _processVersion(version: "VersionItem") -> "bool":
    env.reset(version.project.options)

    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.release.version} ({version.index}/{version.total}).")

        count = 5
        while count > 0:
            count -= 1
            retry = False
            try:
                print(f"    Processing {version.release}.")

                res = version.project.func(version.release, retry)
                assert res.success, "Result is not successful"

                print(f"    Processed {version.release}.")
                return True
            except Exception as ex:
                print(
                    f"    Error for {version.release}: {ex}, retrying")
                retry = True
                sleep(random.random())
    except Exception as ex:
        print(f"  Error for {version.release}: {ex}")

    print(f"  Failed to process {version.release}.")
    return False


def _processProject(project: ProjectItem) -> "list[tuple[Release, bool]]":
    ret = []

    try:
        print(
            f"Process {project.project} ({project.index}/{project.total}).")
        rels = releases.getReleases(project.project)
        totalVersion = len(rels)
        items = []
        for versionIndex, item in enumerate(rels):
            items.append(VersionItem(
                project, versionIndex + 1, totalVersion, item))

        with ProcessPoolExecutor(max_workers=None if project.parallel else 1) as pool:
            results = list(pool.map(_processVersion, items))

        ret = [(rels[i], results[i]) for i in range(len(results))]
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")

    success = sum((1 for i in results if i))
    failed = ', '.join((i[0].version for i in ret if not i[1]))
    print(
        f"Processed {len(ret)} releases for {project.project} (Success: {success}, Failed: {failed or '0'}).")
    return ret


class SingleProcessor:
    def __init__(self, processor: "Callable[[Release, bool], Product]") -> None:
        self.processor = processor

    def processVersion(self, project: "str", version: "str"):
        _processVersion(VersionItem(ProjectItem(
            project, 1, 1, self.processor, env), 1, 1, Release(project, version)))

    def processProject(self, project: "str", parallel: "bool" = True):
        _processProject(ProjectItem(
            project, 1, 1, self.processor, parallel, env))

    def processProjects(self, projects: "list[str]", parallel: "bool" = True, parallelVersion: "bool" = True):
        items = []
        for projectIndex, item in enumerate(projects):
            items.append(ProjectItem(item, projectIndex +
                         1, len(projects), self.processor, parallelVersion, env))

        with ProcessPoolExecutor(max_workers=None if parallel else 1) as pool:
            results = list(pool.map(_processProject, items))

        print(f"Processed {len(results)} projects: {', '.join(projects)}.")
        for i in range(len(results)):
            print(
                f"  {projects[i]}: {sum((1 for b in results[i] if b[1]))}/{len(results[i])}")
