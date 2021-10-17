import pathlib
from typing import Any, List, Optional, Tuple
from ..downloads import index, wheels, releases, mirrors
from ..analyses.environment import analyze
from ..diffs.differ import diff
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProjectItem:
    project: str
    index: str
    total: int


@dataclass
class VersionItem:
    versionOld: str
    versionNew: str
    wheelOld: pathlib.Path
    wheelNew: pathlib.Path
    index: str
    total: int
    project: ProjectItem


def diffVersion(version: VersionItem):
    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.versionOld} & {version.versionNew} ({version.index}/{version.total}).")

        count = 5
        while count > 0:
            count -= 1
            try:
                print(
                    f"    Analyze {version.project.project} @ {version.versionOld}.")
                oldApi = analyze(version.wheelOld)
                print(
                    f"    Analyze {version.project.project} @ {version.versionNew}.")
                newApi = analyze(version.wheelNew)
                print(
                    f"    Diff {version.project.project} @ {version.versionOld} & {version.versionNew}.")
                diff(oldApi, newApi)
                count = 0
            except Exception as ex:
                print(
                    f"Error for {version.project.project} @ {version.versionOld} & {version.versionNew}: {ex}, retrying")
    except Exception as ex:
        print(
            f"Error for {version.project.project} @ {version.versionOld} & {version.versionNew}: {ex}")


def diffProject(project: ProjectItem):
    try:
        print(f"Process {project.project} ({project.index}/{project.total}).")
        rels = releases.getReleases(project.project)
        downloadedVersion: List[Tuple[str, str]] = []
        for version in rels.keys():
            info = releases.getDownloadInfo(rels[version])
            if info:
                wheel = wheels.downloadWheel(
                    info, mirror=mirrors.FILE_TSINGHUA)
                downloadedVersion.append((version, wheel))
        if len(downloadedVersion) <= 1:
            print(
                f"No enough download version for {project.project} ({project.index}/{project.total}).")
            return
        items = []
        lastVersion: Optional[Tuple[str, str]] = None
        total = len(downloadedVersion) - 1
        for versionIndex, item in enumerate(downloadedVersion):
            version, wheel = item
            if lastVersion is None:
                pass
            else:
                items.append(VersionItem(lastVersion[0], version, lastVersion[1], wheel, versionIndex,total, project))
            lastVersion = item

        with ProcessPoolExecutor() as pool:
            pool.map(diffVersion, items)
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")


def diffProjects(projects: List[str]):
    items=[]
    for projectIndex, item in enumerate(projects):
        items.append(ProjectItem(item, projectIndex+1, len(projects)))

    with ProcessPoolExecutor() as pool:
        pool.map(diffProject, items)
