import textwrap
from abc import ABC, abstractmethod

from ...models import ApiDescription


class Enricher(ABC):
    @abstractmethod
    def enrich(self, /, api: ApiDescription) -> None: ...


def clearSrc(src: str):
    # May lead to bug if use """something in long string"""
    lines = src.splitlines(keepends=True)
    return textwrap.dedent(
        "".join((line for line in lines if not line.lstrip().startswith("#")))
    )
