import shutil
import zipfile
from dataclasses import dataclass, field
from email.message import Message
from email.parser import Parser
from logging import Logger
from pathlib import Path
from typing import override

from .. import getCacheDirectory, utils
from . import PYVERSION_LOWER, PYVERSION_UPPER, Preprocessor

FILE_ORIGIN = "https://files.pythonhosted.org/"
FILE_TSINGHUA = "https://pypi.tuna.tsinghua.edu.cn/"
INDEX_ORIGIN = "https://pypi.org/simple/"
INDEX_TSINGHUA = "https://pypi.tuna.tsinghua.edu.cn/simple/"


def readPackageInfo(path: Path):
    return Parser().parsestr(path.read_text())


@dataclass
class CompatibilityTag:
    python: str = "py3"
    abi: str = "none"
    platform: list[str] = field(default_factory=lambda: ["any"])

    @classmethod
    def fromfile(cls, /, filename: str):
        filename = Path(filename).stem
        try:
            segs = filename.split("-")
            return CompatibilityTag(segs[-3], segs[-2], segs[-1].split("."))
        except:
            return None


@dataclass
class DistInfo:
    metadata: Message
    topLevel: list[str]
    wheel: Message

    @property
    def name(self, /):
        return str(self.metadata.get("name"))

    @property
    def version(self, /):
        return str(self.metadata.get("version"))

    @property
    def dependencies(self, /):
        dist = self.metadata.get_all("requires-dist")
        if dist:
            return [str(t).split(maxsplit=1)[0] for t in dist]
        else:
            return []

    @property
    def pyversion(self, /) -> str | None:
        tags = self.wheel.get_all("tag")
        if tags:
            for rawTag in tags:
                tag = CompatibilityTag.fromfile(rawTag) or CompatibilityTag()
                if "any" in tag.platform:
                    requires = str(self.metadata.get("requires-python"))
                    requires = list(map(lambda x: x.strip(), requires.split(",")))
                    if len(requires) == 0:
                        return None
                    for item in requires:
                        if item.startswith(">="):
                            version = item.removeprefix(">=").strip()
                            if version.startswith("3."):
                                return f"3.{PYVERSION_UPPER}"
                            else:
                                continue
                        elif item.startswith("<="):
                            return item.removeprefix("<=").strip()
                    return f"3.{PYVERSION_UPPER}"
                else:
                    for i in range(PYVERSION_UPPER, PYVERSION_LOWER - 1, -1):
                        if f"py3{i}" in tag.python or f"cp3{i}" in tag.python:
                            return f"3.{i}"
        return f"3.{PYVERSION_UPPER}"

    @classmethod
    def fromdir(cls, /, path: Path, project: str = ""):
        distinfoDir = list(path.glob(f"{project.replace('-', '_')}*.dist-info"))
        if len(distinfoDir) == 0:
            return None
        distinfoDir = distinfoDir[0]
        try:
            metadata: Message = readPackageInfo(distinfoDir / "METADATA")
            tp = distinfoDir / "top_level.txt"

            if tp.exists():
                toplevel = [s.strip() for s in tp.read_text().splitlines() if s.strip()]
            else:
                toplevel = []

            return DistInfo(
                metadata=metadata,
                topLevel=toplevel,
                wheel=readPackageInfo(distinfoDir / "WHEEL"),
            )
        except:
            return None


def unpackWheel(wheelFile: Path, targetDir: Path):
    utils.ensureDirectory(targetDir)
    with zipfile.ZipFile(wheelFile) as f:
        f.extractall(targetDir)


class WheelUnpackPreprocessor(Preprocessor):
    def __init__(self, /, cacheDir: Path | None, logger: Logger | None = None):
        super().__init__(logger)
        self.cacheDir = cacheDir or getCacheDirectory()
        utils.ensureDirectory(self.cacheDir)

    @override
    def preprocess(self, /, product):
        assert (
            product.wheelFile and product.wheelFile.exists()
        ), "No wheel file provided."

        targetDir = self.cacheDir / product.wheelFile.stem
        if targetDir.exists():
            self.logger.warning(f"Remove unpacked directory {targetDir}")
            shutil.rmtree(targetDir)

        self.logger.debug(f"Unpacking {product.wheelFile} to {targetDir}")
        unpackWheel(product.wheelFile, targetDir)
        self.logger.info(f"Unpacked {product.wheelFile} to {targetDir}")
        product.rootPath = targetDir


class WheelMetadataPreprocessor(Preprocessor):
    @override
    def preprocess(self, /, product):
        assert product.rootPath, "No root path provided."

        self.logger.debug(
            f"Load dist-info from {product.rootPath} for {product.release.project}"
        )

        distInfo = DistInfo.fromdir(product.rootPath, product.release.project)

        self.logger.info(f"Loaded dist-info from {product.rootPath}: {distInfo}")

        if distInfo:
            if distInfo.pyversion:
                if not product.pyversion:
                    product.pyversion = distInfo.pyversion
            if distInfo.name:
                if product.release.project:
                    assert (
                        product.release.project == distInfo.name
                    ), "Different name between release and dist-info."
                else:
                    product.release = product.release.model_copy(
                        update={"project": distInfo.name}
                    )
            if distInfo.version:
                if product.release.version:
                    assert (
                        product.release.version == distInfo.version
                    ), "Different version between release and dist-info."
                else:
                    product.release = product.release.model_copy(
                        update={"version": distInfo.version}
                    )
            product.topModules.extend(distInfo.topLevel)
            product.dependencies.extend(distInfo.dependencies)
            if distInfo.metadata:
                product.description = str(distInfo.metadata.get_payload())
                product.metadata = [(x, str(y)) for x, y in distInfo.metadata.items()]
