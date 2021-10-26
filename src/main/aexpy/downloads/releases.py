import json
from dataclasses import dataclass, field
from urllib import parse
import requests
import pathlib

from .. import fsutils
from ..env import env


@dataclass
class DownloadInfo:
    url: str
    sha256: str = ""
    md5: str = ""
    name: str = field(init=False)

    def __post_init__(self):
        self.name = parse.urlparse(self.url).path.split("/")[-1]


@dataclass
class CompatibilityTag:
    python: str = "py3"
    abi: str = "none"
    platform: str = "any"


def getCompatibilityTag(filename: str) -> CompatibilityTag:
    filename = pathlib.Path(filename).stem
    try:
        segs = filename.split("-")
        return CompatibilityTag(segs[-3], segs[-2], segs[-1])
    except:
        return CompatibilityTag()


def getReleaseInfo(project: str, version: str) -> dict | None:
    cache = env.cache.joinpath("releases").joinpath(project)
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{version}.json")
    if not cacheFile.exists() or env.redo:
        try:
            cacheFile.write_text(json.dumps(
                requests.get(
                    f"https://pypi.org/pypi/{project}/{version}/json", timeout=60)
                .json()["info"]))
        except:
            cacheFile.write_text(json.dumps(None))
    return json.loads(cacheFile.read_text())


def getReleases(project: str) -> dict | None:
    cache = env.cache.joinpath("releases").joinpath(project)
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"index.json")

    if not cacheFile.exists() or env.redo:
        try:
            cacheFile.write_text(json.dumps(
                requests.get(
                    f"https://pypi.org/pypi/{project}/json", timeout=60)
                .json()["releases"]))
        except:
            cacheFile.write_text(json.dumps(None))

    return json.loads(cacheFile.read_text())


def getDownloadInfo(release: list[dict], packagetype="bdist_wheel") -> DownloadInfo | None:
    py3=[]

    for item in release:
        if item["packagetype"] != packagetype:
            continue

        # https://www.python.org/dev/peps/pep-0425/#compressed-tag-sets

        tag=getCompatibilityTag(item["filename"])
        if "py3" not in tag.python:
            if "cp3" not in tag.python:
                continue
        if "any" not in tag.platform:
            if "linux" not in tag.platform or "x86_64" not in tag.platform:
                continue

        py3.append((item, tag))

    py37=[]
    for item, tag in py3:
        for i in range(7, 11):
            if f"py3{i}" in tag.python:
                py37.append(item)
                break

    result=None

    if len(py37) > 0:
        result=py37[0]

    if len(py3) > 0:
        result=py3[0][0]

    if result:
        return DownloadInfo(item["url"], item["digests"].get("sha256", ""), item["digests"].get("md5", ""))

    return None
