from dataclasses import dataclass
import logging
import textwrap
from abc import ABC, abstractmethod
import pathlib

from aexpy.downloads.wheels import DistInfo

from ..models import ApiCollection


@dataclass
class AnalysisInfo:
    wheel: pathlib.Path
    unpacked: pathlib.Path
    distinfo: DistInfo
    cache: pathlib.Path
    log: pathlib.Path

    def src(self) -> list[pathlib.Path]:
        return [self.unpacked.joinpath(item) for item in self.distinfo.topLevel]


class Enricher(ABC):
    @abstractmethod
    def enrich(api: ApiCollection) -> None:
        pass


def clearSrc(src: str):
    # May lead to bug if use """something in long string"""
    lines = src.splitlines(keepends=True)
    return textwrap.dedent("".join((line for line in lines if not line.lstrip().startswith("#"))))
