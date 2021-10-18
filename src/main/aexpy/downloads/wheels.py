from email.message import Message
import pathlib
from typing import Dict, List, Optional, Tuple
from urllib import request, parse
import zipfile
import hashlib
import json
from dataclasses import dataclass
import wheel.metadata

from .mirrors import FILE_ORIGIN, FILE_TSINGHUA
from .. import fsutils
from ..env import env
from .releases import DownloadInfo


@dataclass
class DistInfo:
    metadata: Message
    topLevel: str
    wheel: Message


def downloadWheel(info: DownloadInfo, mirror: str = FILE_ORIGIN) -> pathlib.Path:
    cache = env.cache.joinpath("wheels")
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(info.name)

    url = info.url.replace(FILE_ORIGIN, mirror)

    if not cacheFile.exists():
        try:
            with request.urlopen(url, timeout=60) as response:
                content = response.read()

                if info.sha256:
                    if hashlib.sha256(content).hexdigest() != info.sha256:
                        raise Exception(
                            f"Release download sha256 mismatch: {info}.")

                if info.md5:
                    if hashlib.md5(content).hexdigest() != info.md5:
                        raise Exception(
                            f"Release download md5 mismatch: {info}.")

                with open(cacheFile, "wb") as file:
                    file.write(content)
        except:
            raise Exception(f"Not found download: {url}.")
    return cacheFile.absolute()


def unpackWheel(path: pathlib.Path) -> pathlib.Path:
    cache = env.cache.joinpath("wheels").joinpath("unpacked")
    cacheDir = cache.joinpath(path.stem)

    if not cacheDir.exists():
        fsutils.ensureDirectory(cacheDir)

        with zipfile.ZipFile(path) as f:
            f.extractall(cacheDir)

    return cacheDir.absolute()


def getDistInfo(unpackedPath: pathlib.Path) -> Optional[DistInfo]:
    distinfoDir = list(unpackedPath.glob("*.dist-info"))
    if len(distinfoDir) == 0:
        return None
    distinfoDir = distinfoDir[0]
    try:
        return DistInfo(
            metadata=wheel.metadata.read_pkg_info(
                distinfoDir.joinpath("METADATA")),
            topLevel=distinfoDir.joinpath("top_level.txt").read_text().strip(),
            wheel=wheel.metadata.read_pkg_info(distinfoDir.joinpath("WHEEL"))
        )
    except:
        return None


def getAvailablePythonVersion(distInfo: DistInfo) -> Optional[str]:
    requires = str(distInfo.metadata.get("requires-python"))
    requires = list(map(lambda x: x.strip(), requires.split(",")))
    if len(requires) == 0:
        return None
    for item in requires:
        if item.startswith(">="):
            return item.lstrip(">=").strip()
        elif item.startswith("<="):
            return item.lstrip("<=").strip()
    return "3.7"
