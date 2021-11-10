from abc import ABC, abstractmethod
import textwrap
import logging

from ..models import ApiCollection


class Enricher(ABC):
    @abstractmethod
    def enrich(api: ApiCollection, logger: logging.Logger | None = None):
        pass


def clearSrc(src: str):
    # May lead to bug if use """something in long string"""
    lines = src.splitlines(keepends=True)
    return textwrap.dedent("".join((line for line in lines if not line.lstrip().startswith("#"))))
