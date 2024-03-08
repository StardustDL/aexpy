import hashlib
import logging
import os
import platform
import subprocess
import urllib.request
from dataclasses import dataclass, field
from logging import Logger
from pathlib import Path
from typing import override
from urllib import parse

from pip import __version__

from .. import getCacheDirectory, utils
from ..models import Release
from . import PYVERSION_LOWER, PYVERSION_UPPER, Preprocessor
from .pypi import (FILE_ORIGIN, FILE_TSINGHUA, INDEX_ORIGIN, INDEX_TSINGHUA,
                   getReleases)
from .wheel import CompatibilityTag

PYVERSIONS = [f"3.{i}" for i in range(PYVERSION_UPPER, PYVERSION_LOWER - 1, -1)]


def wheelByPip(
    release: Release,
    path: Path,
    pyversions: list[str] | None = None,
    logger: Logger | None = None,
    mirror: bool = False,
) -> tuple[Path, str]:
    logger = logger or logging.getLogger("pre-download-pip")
    index = INDEX_TSINGHUA if mirror else INDEX_ORIGIN
    pyversions = pyversions or PYVERSIONS

    def glob(suffix: str):
        prefix = f"{release.project}-{release.version}".lower()
        prefix2 = f"{release.project.replace('-', '_')}-{release.version}".lower()

        def check(s: str):
            t = s.lower()
            return (
                t == prefix
                or t == prefix2
                or t.startswith(prefix + "-")
                or t.startswith(prefix2 + "-")
            )

        return list(
            (i for i in path.glob(f"*{suffix}") if check(i.name.removesuffix(suffix)))
        )

    for item in glob(".whl"):
        logger.warning(f"Remove downloaded {item}.")
        os.remove(item)

    for pyversion in pyversions:
        logger.debug(f"Download wheel distribution for Python {pyversion}.")
        try:
            subres = subprocess.run(
                [
                    "pip",
                    "download",
                    "--python-version",
                    pyversion,
                    f"{release.project}=={release.version}",
                    "--no-deps",
                    "--only-binary",
                    ":all:",
                    "-i",
                    index,
                ],
                cwd=path,
                capture_output=True,
                text=True,
            )
            logger.debug(
                f"Inner pip download wheel for Python {pyversion} exit with {subres.returncode}."
            )
            utils.logProcessResult(logger, subres)

            subres.check_returncode()

            files = glob(".whl")
            assert len(files) > 0
            return files[0].resolve(), pyversion
        except Exception:
            logger.error(
                f"Failed to download for Python {pyversion} wheel for {release}",
                exc_info=True,
            )

    for item in glob(".tar.gz"):
        logger.debug(f"Remove downloaded {item}.")
        os.remove(item)

    for pyversion in PYVERSIONS:
        logger.debug(f"Download source distribution for Python {pyversion}.")
        try:
            subres = subprocess.run(
                [
                    "pip",
                    "download",
                    "--python-version",
                    pyversion,
                    f"{release.project}=={release.version}",
                    "--no-deps",
                    "--no-binary",
                    ":all:",
                    "-i",
                    index,
                ],
                cwd=path,
                capture_output=True,
                text=True,
            )
            logger.debug(
                f"Inner pip download sdist for Python {pyversion} exit with {subres.returncode}."
            )
            utils.logProcessResult(logger, subres)

            subres.check_returncode()

            files = glob(".tar.gz")
            assert len(files) > 0

            logger.debug(
                f"Build wheel distribution for Python {pyversion}: {files[0]}."
            )
            subres = subprocess.run(
                f"pip wheel {release.project}=={release.version} --no-deps -i {index}",
                cwd=path,
                capture_output=True,
                text=True,
            )
            logger.debug(f"Inner pip wheel {files[0]} exit with {subres.returncode}.")
            utils.logProcessResult(logger, subres)

            subres.check_returncode()

            files = glob(".whl")
            assert len(files) > 0

            return files[0].resolve(), pyversion
        except Exception:
            logger.error(
                f"Failed to download source dist for Python {pyversion} for {release}",
                exc_info=True,
            )

    raise Exception(f"Failed to download wheel for {release}.")


@dataclass
class DownloadInfo:
    url: str
    sha256: str = ""
    md5: str = ""
    name: str = field(init=False)

    def __post_init__(self, /):
        self.name = parse.urlparse(self.url).path.split("/")[-1]


def wheelByHttp(
    release: Release, path: Path, logger: Logger | None, mirror: bool = False
) -> Path:
    logger = logger or logging.getLogger("pre-download-http")

    rels = getReleases(release.project)
    if rels is None or release.version not in rels:
        rels = getReleases(release.project)
    if rels is None or release.version not in rels:
        raise Exception(f"Not found the release {release}")
    download = getDownloadInfo(rels[release.version])
    if download is None:
        raise Exception(f"Not found the valid distribution {release}")
    return downloadRawWheel(download, path, logger, mirror)


def getDownloadInfo(
    release: list[dict], packagetype="bdist_wheel"
) -> DownloadInfo | None:
    py3 = []

    for item in release:
        if item["packagetype"] != packagetype:
            continue

        # https://www.python.org/dev/peps/pep-0425/#compressed-tag-sets

        tag = CompatibilityTag.fromfile(item["filename"]) or CompatibilityTag()
        if "py3" not in tag.python:
            if "cp3" not in tag.python:
                continue
        if "any" not in tag.platform:
            if "windows" in platform.platform().lower():
                if not any(
                    (
                        platform
                        for platform in tag.platform
                        if "win" in platform and "amd64" in platform
                    )
                ):
                    continue
            else:
                if not any(
                    (
                        platform
                        for platform in tag.platform
                        if "linux" in platform and "x86_64" in platform
                    )
                ):
                    continue

        py3.append((item, tag))

    supportedPy = []
    for item, tag in py3:
        for i in range(PYVERSION_UPPER, PYVERSION_LOWER - 1, -1):
            if f"py3{i}" in tag.python or f"cp3{i}" in tag.python:
                supportedPy.append(item)
                break

    result = None

    if len(supportedPy) > 0:
        result = supportedPy[0]

    if len(py3) > 0:
        result = py3[0][0]

    if result:
        ret = DownloadInfo(
            result["url"],
            result["digests"].get("sha256", ""),
            result["digests"].get("md5", ""),
        )
        return ret

    return None


def downloadRawWheel(
    info: DownloadInfo, path: Path, logger: Logger, mirror: bool = False
) -> Path:
    cacheFile = path / info.name

    if mirror:
        url = info.url.replace(FILE_ORIGIN, FILE_TSINGHUA)
    else:
        url = info.url

    if not cacheFile.exists():
        logger.debug(f"Download wheel @ {url}.")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=60) as res:
                content = res.read()
            if info.sha256:
                if hashlib.sha256(content).hexdigest() != info.sha256:
                    raise Exception(f"Release download sha256 mismatch: {info}.")

            if info.md5:
                if hashlib.md5(content).hexdigest() != info.md5:
                    raise Exception(f"Release download md5 mismatch: {info}.")

            with open(cacheFile, "wb") as file:
                file.write(content)
        except Exception as ex:
            logger.error(f"Not found wheel {url}.", exc_info=True)
            raise Exception(f"Not found download: {url}.") from ex

    return cacheFile.resolve()


class PipWheelDownloadPreprocessor(Preprocessor):
    def __init__(
        self,
        /,
        cacheDir: Path | None,
        mirror: bool = False,
        logger: Logger | None = None,
    ):
        super().__init__(logger)
        self.mirror = mirror
        self.cacheDir = cacheDir or getCacheDirectory()
        self.name = self.cls() + f"+pip@{__version__}"
        utils.ensureDirectory(self.cacheDir)

    @override
    def preprocess(self, /, product):
        if product.pyversion:
            pyversions = [product.pyversion] + PYVERSIONS
        else:
            pyversions = None
        wheelFile, pyversion = wheelByPip(
            product.release, self.cacheDir, pyversions, logger=self.logger
        )
        product.pyversion = pyversion
        product.wheelFile = wheelFile
