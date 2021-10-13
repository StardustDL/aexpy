from typing import Dict, List, Optional
from urllib import request, parse
from dataclasses import dataclass, field
import json

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


def getReleaseInfo(project: str, version: str) -> Optional[Dict]:
    cache = env.cache.joinpath("releases").joinpath(project)
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{version}.json")
    if not cacheFile.exists():
        try:
            with request.urlopen(f"https://pypi.org/pypi/{project}/{version}/json", timeout=60) as response:
                cacheFile.write_text(json.dumps(json.loads(
                    response.read().decode("utf-8"))["info"]))
        except:
            cacheFile.write_text(json.dumps(None))
    return json.loads(cacheFile.read_text())


def getReleases(project: str) -> Optional[Dict]:
    cache = env.cache.joinpath("releases").joinpath(project)
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"index.json")

    if not cacheFile.exists():
        try:
            with request.urlopen(f"https://pypi.org/pypi/{project}/json", timeout=60) as response:            
                cacheFile.write_text(json.dumps(json.loads(
                    response.read().decode("utf-8"))["releases"]))
        except:
            cacheFile.write_text(json.dumps(None))

    return json.loads(cacheFile.read_text())




def getDownloadInfo(release: List[Dict], packagetype="bdist_wheel") -> Optional[DownloadInfo]:
    for item in release:
        if item["packagetype"] == packagetype:
            return DownloadInfo(item["url"], item["digests"].get("sha256", ""), item["digests"].get("md5", ""))
    return None
