import hashlib
import json
import pathlib
import shutil
import zipfile
from dataclasses import dataclass
from email.message import Message

import requests
import wheel.metadata

import logging

from .. import fsutils
from ..env import env
from .mirrors import FILE_ORIGIN, FILE_TSINGHUA
from .releases import CompatibilityTag, DownloadInfo, getCompatibilityTag, getReleases, getDownloadInfo

logger = logging.getLogger("download-wheel")


@dataclass
class DistInfo:
    metadata: Message
    topLevel: list[str]
    wheel: Message


def downloadWheel(info: DownloadInfo, mirror: str = FILE_ORIGIN) -> pathlib.Path:
    cache = env.cache.joinpath("wheels")
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(info.name)

    url = info.url.replace(FILE_ORIGIN, mirror)

    if not cacheFile.exists() or env.redo:

        logger.info(f"Download wheel @ {url}.")
        try:
            content = requests.get(url, timeout=60).content
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
        except Exception as ex:
            logger.error(f"Not found wheel {url}.", exc_info=ex)
            raise Exception(f"Not found download: {url}.")
    return cacheFile.absolute()


def unpackWheel(path: pathlib.Path) -> pathlib.Path:
    cache = env.cache.joinpath("wheels").joinpath("unpacked")
    cacheDir = cache.joinpath(path.stem)

    if env.redo and cacheDir.exists():
        logger.info(
            f"Remove old unpacked files @ {cacheDir.relative_to(env.cache)}")
        shutil.rmtree(cacheDir)

    if not cacheDir.exists() or env.redo:
        fsutils.ensureDirectory(cacheDir)

        logger.info(
            f"Unpack {path.relative_to(env.cache)} to {cacheDir.relative_to(env.cache)}")

        with zipfile.ZipFile(path) as f:
            f.extractall(cacheDir)

    return cacheDir.absolute()


def getUnpackPath(project: str, version: str) -> pathlib.Path | None:
    rels = getReleases(project)
    if rels is None or version not in rels:
        return None
    download = getDownloadInfo(rels[version])
    if download is None:
        return None
    try:
        wheel = downloadWheel(
            download, mirror=FILE_TSINGHUA)
        unpack = unpackWheel(wheel)
        return unpack
    except Exception as ex:
        logger.error("Failed to get unpack path.", exc_info=ex)
        return None


def getDistInfo(unpackedPath: pathlib.Path) -> DistInfo | None:
    distinfoDir = list(unpackedPath.glob("*.dist-info"))
    if len(distinfoDir) == 0:
        return None
    distinfoDir = distinfoDir[0]
    try:
        return DistInfo(
            metadata=wheel.metadata.read_pkg_info(
                distinfoDir.joinpath("METADATA")),
            topLevel=[s.strip() for s in distinfoDir.joinpath(
                "top_level.txt").read_text().splitlines() if s.strip()],
            wheel=wheel.metadata.read_pkg_info(distinfoDir.joinpath("WHEEL"))
        )
    except:
        return None


def getSourcePaths(unpackedPath: pathlib.Path, distInfo: DistInfo | None = None) -> list[pathlib.Path] | None:
    if distInfo is None:
        distInfo = getDistInfo(unpackedPath)
    if distInfo is None:
        return None
    return [unpackedPath.joinpath(item) for item in distInfo.topLevel]


def getAvailablePythonVersion(distInfo: DistInfo) -> str | None:
    tags = distInfo.wheel.get_all("tag")
    for rawTag in tags:
        tag = getCompatibilityTag(rawTag)
        if "any" in tag.platform:
            requires = str(distInfo.metadata.get("requires-python"))
            requires = list(map(lambda x: x.strip(), requires.split(",")))
            if len(requires) == 0:
                return None
            for item in requires:
                if item.startswith(">="):
                    try:
                        version = item.lstrip(">=").strip()
                        value = float(version)
                        if value < 3.7:
                            return "3.7"
                        else:
                            return version
                    except:
                        return "3.7"
                elif item.startswith("<="):
                    return item.lstrip("<=").strip()
            return "3.7"
        else:
            for i in range(7, 11):
                if f"py3{i}" in tag.python or f"cp3{i}" in tag.python:
                    return f"3.{i}"
    return None
