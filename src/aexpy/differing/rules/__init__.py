
import functools
import itertools
from itertools import zip_longest
from typing import Callable, OrderedDict

from aexpy.models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                      CollectionEntry, FunctionEntry, ModuleEntry,
                                      Parameter, ParameterKind, SpecialEntry, SpecialKind)
from aexpy.models.difference import DiffEntry

from ..checkers import (DiffRule, DiffRuleCollection,
                        diffrule, fortype)


def add(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if a is None and b is not None:
        return [DiffEntry(message=f"Add {b.__class__.__name__.removesuffix('Entry')}: {b.id}.")]
    return []


def remove(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if a is not None and b is None:
        return [DiffEntry(message=f"Remove {a.__class__.__name__.removesuffix('Entry').lower()}: {a.id}.")]
    return []
