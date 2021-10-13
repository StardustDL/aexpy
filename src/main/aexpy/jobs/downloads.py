from typing import Any, List
from ..downloads import index, wheels, releases, mirrors
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
    version: str
    index: str
    total: int
    release: Any
    project: ProjectItem


def downloadVersion(version: VersionItem):
    try:
        print(f"  Process {version.project.project} ({version.project.index}/{version.project.total}) @ {version.version} ({version.index}/{version.total}).")
        info = releases.getReleaseInfo(version.project.project, version.version)
        download = releases.getDownloadInfo(version.release)
        if download:
            count = 5
            while count > 0:
                count -= 1
                try:
                    print(f"    Download {version.project.project} @ {version.version}.")
                    wheel = wheels.downloadWheel(download, mirror=mirrors.FILE_TSINGHUA)
                    print(f"      {wheel}")
                    print(f"    Unpack {version.project.project} @ {version.version}.")
                    unpack = wheels.unpackWheel(wheel)
                    print(f"      {unpack}")
                    count = 0
                except Exception as ex:
                    print(f"Error for {version.project.project} @ {version.version}: {ex}, retrying")
    except Exception as ex:
        print(f"Error for {version.project.project} @ {version.version}: {ex}")


def downloadProject(project: ProjectItem):
    try: 
        print(f"Process {project.project} ({project.index}/{project.total}).")
        rels = releases.getReleases(project.project)
        versions = list(rels.items())
        totalVersion = len(versions)
        items = []
        for versionIndex, item in enumerate(versions):
            version, release = item
            items.append(VersionItem(version, versionIndex+1, totalVersion, release, project))
        
        with ProcessPoolExecutor() as pool:
            pool.map(downloadVersion, items)
    except Exception as ex:
        print(f"Error for {project.project}: {ex}")


def downloadProjects(projects: List[str]):
    items = []
    for projectIndex, item in enumerate(projects):
        items.append(ProjectItem(item, projectIndex+1, len(projects)))

    with ProcessPoolExecutor() as pool:
        pool.map(downloadProject, items)
