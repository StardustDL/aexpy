from typing import Iterable

from ....models import ApiDescription
from ....models.description import ApiEntry
from ....models.difference import DiffEntry


def add(
    a: ApiEntry | None,
    b: ApiEntry | None,
    old: ApiDescription,
    new: ApiDescription,
) -> Iterable[DiffEntry]:
    if a is None and b is not None:
        if b.parent in old and b.parent in new:
            # only report if parent exisits in old version
            yield DiffEntry(
                message=f"Add {b.__class__.__name__.removesuffix('Entry').lower()} ({b.parent}): {b.name}."
            )


def remove(
    a: ApiEntry | None,
    b: ApiEntry | None,
    old: ApiDescription,
    new: ApiDescription,
) -> Iterable[DiffEntry]:
    if a is not None and b is None:
        if a.parent in old and a.parent in new:
            # only report if parent still exisits
            yield DiffEntry(
                message=f"Remove {a.__class__.__name__.removesuffix('Entry').lower()} ({a.parent}): {a.name}."
            )
