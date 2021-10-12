import pathlib
from typing import Dict, List, Optional
from urllib import request, parse
import zipfile
import hashlib
import json

from .mirrors import FILE_ORIGIN, FILE_TSINGHUA
from .. import fsutils
from ..env import env
from .releases import DownloadInfo


def downloadWheel(info: DownloadInfo, mirror: str = FILE_ORIGIN) -> pathlib.Path:
    cache = env.cache.joinpath("wheels")
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(info.name)
    
    url = info.url.replace(FILE_ORIGIN, mirror)

    if not cacheFile.exists():
        with request.urlopen(url, timeout=60) as response:
            if response.status != 200:
                raise Exception(f"Not found download: {url}.")

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
    return cacheFile.absolute()


def unpackWheel(path: pathlib.Path) -> pathlib.Path:
    cache = env.cache.joinpath("wheels").joinpath("unpacked")
    cacheDir = cache.joinpath(path.stem)

    if not cacheDir.exists():
        fsutils.ensureDirectory(cacheDir)

        with zipfile.ZipFile(path) as f:
            f.extractall(cacheDir)    
    
    return cacheDir
