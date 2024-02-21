from typing import Iterable
from aexpy.models import ApiDescription

from aexpy.models.description import ApiEntry
from aexpy.models.difference import DiffEntry


def add(
    a: ApiEntry | None,
    b: ApiEntry | None,
    old: ApiDescription,
    new: ApiDescription,
) -> Iterable[DiffEntry]:
    if a is None and b is not None:
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
        if a.parent in old and a.parent not in new:
            # only report if parent exisits
            return
        yield DiffEntry(
            message=f"Remove {a.__class__.__name__.removesuffix('Entry').lower()} ({a.parent}): {a.name}."
        )
