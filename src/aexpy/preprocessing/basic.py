import hashlib
import platform
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.message import Message
from logging import Logger
from pathlib import Path
from urllib import parse

import requests
import wheel.metadata

from aexpy import json, utils
from aexpy.producer import ProducerOptions

from ..models import Distribution, Release
from ..utils import elapsedTimer, ensureDirectory, logWithFile
from .wheel import (FILE_ORIGIN, FILE_TSINGHUA, CompatibilityTag,
                    WheelPreprocessor)


@dataclass
class DownloadInfo:
    url: "str"
    sha256: "str" = ""
    md5: "str" = ""
    name: "str" = field(init=False)

    def __post_init__(self):
        self.name = parse.urlparse(self.url).path.split("/")[-1]


class BasicPreprocessor(WheelPreprocessor):
    def downloadWheel(self, distribution: "Distribution", path: "Path") -> "Path":
        release = distribution.release
        rels = self.getReleases(release.project)
        if rels is None or release.version not in rels:
            raise Exception(f"Not found the release {release}")
        download = self.getDownloadInfo(rels[release.version])
        if download is None:
            raise Exception(
                f"Not found the valid distribution {release}")
        return self.downloadRawWheel(release.project, download, path)

    def getDownloadInfo(self, release: "list[dict]", packagetype="bdist_wheel") -> "DownloadInfo | None":
        py3 = []

        for item in release:
            if item["packagetype"] != packagetype:
                continue

            # https://www.python.org/dev/peps/pep-0425/#compressed-tag-sets

            tag = CompatibilityTag.fromfile(
                item["filename"]) or CompatibilityTag()
            if "py3" not in tag.python:
                if "cp3" not in tag.python:
                    continue
            if "any" not in tag.platform:
                if "windows" in platform.platform().lower():
                    if not any((platform for platform in tag.platform if "win" in platform and "amd64" in platform)):
                        continue
                else:
                    if not any((platform for platform in tag.platform if "linux" in platform and "x86_64" in platform)):
                        continue

            py3.append((item, tag))

        py37 = []
        for item, tag in py3:
            for i in range(7, 11):
                if f"py3{i}" in tag.python or f"cp3{i}" in tag.python:
                    py37.append(item)
                    break

        result = None

        if len(py37) > 0:
            result = py37[0]

        if len(py3) > 0:
            result = py3[0][0]

        if result:
            ret = DownloadInfo(result["url"], result["digests"].get(
                "sha256", ""), result["digests"].get("md5", ""))
            self.logger.debug(f"Select download-info {ret}.")
            return ret

        self.logger.warning(f"Failed to select download-info.")
        return None

    def downloadRawWheel(self, project: str, info: "DownloadInfo", path: "Path") -> "Path":
        cacheFile = path / info.name

        if self.mirror:
            url = info.url.replace(FILE_ORIGIN, FILE_TSINGHUA)
        else:
            url = info.url

        if not cacheFile.exists() or self.options.redo:
            self.logger.info(f"Download wheel @ {url}.")
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
                self.logger.error(f"Not found wheel {url}.", exc_info=ex)
                raise Exception(f"Not found download: {url}.")

        return cacheFile.resolve()
