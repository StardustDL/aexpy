import pathlib
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Tuple

from ..analyses.environment import analyze
from ..diffs.environment import diff
from ..downloads import index, mirrors, releases, wheels
from ..env import Environment, env

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProjectItem:
    project: str
    index: str
    total: int
    env: Environment


@dataclass
class VersionItem:
    versionOld: str
    versionNew: str
    wheelOld: pathlib.Path
    wheelNew: pathlib.Path
    index: str
    total: int
    project: ProjectItem


def setEnv(value: Environment):
    from ..env import env

    env.setPath(value.path)
    env.docker = value.docker
    env.redo = value.redo
    env.interactive = value.interactive


def _diffVersion(version: VersionItem):
    setEnv(version.project.env)
    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.versionOld} & {version.versionNew} ({version.index}/{version.total}).")

        count = 3
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


def _diffProject(project: ProjectItem):
    setEnv(project.env)

    try:
        print(f"Process {project.project} ({project.index}/{project.total}).")
        rels = releases.getReleases(project.project)
        downloadedVersion: list[Tuple[str, str]] = []
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
        lastVersion: Tuple[str, str] | None = None
        total = len(downloadedVersion) - 1
        for versionIndex, item in enumerate(downloadedVersion):
            version, wheel = item
            if lastVersion is None:
                pass
            else:
                items.append(VersionItem(
                    lastVersion[0], version, lastVersion[1], wheel, versionIndex, total, project))
            lastVersion = item

        with ProcessPoolExecutor() as pool:
            pool.map(_diffVersion, items)
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")


def diffVersion(project: str, old: str, new: str):
    rels = releases.getReleases(project.project)
    if old not in rels:
        raise Exception(f"No release {project} @ {old}")

    oldInfo = releases.getDownloadInfo(rels[old])
    if not oldInfo:
        raise Exception(f"No download info for {project} @ {old}.")

    oldWheel = wheels.downloadWheel(oldInfo, mirror=mirrors.FILE_TSINGHUA)

    if new not in rels:
        raise Exception(f"No release {project} @ {new}")

    newInfo = releases.getDownloadInfo(rels[new])
    if not newInfo:
        raise Exception(f"No download info for {project} @ {new}.")

    newWheel = wheels.downloadWheel(newInfo, mirror=mirrors.FILE_TSINGHUA)

    _diffVersion(VersionItem(old, new, oldWheel, newWheel,
                 1, 1, ProjectItem(project, 1, 1, env)))


def diffProject(project: str):
    _diffProject(ProjectItem(project, 1, 1, env))


def diffProjects(projects: list[str]):
    items = []
    for projectIndex, item in enumerate(projects):
        items.append(ProjectItem(item, projectIndex+1, len(projects), env))

    with ProcessPoolExecutor() as pool:
        pool.map(_diffProject, items)
