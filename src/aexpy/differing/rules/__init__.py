
import functools
import itertools
from itertools import zip_longest
from typing import Callable, OrderedDict
from aexpy.models import ApiDescription

from aexpy.models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                      CollectionEntry, FunctionEntry, ItemEntry,
                                      ModuleEntry, Parameter, ParameterKind,
                                      SpecialEntry, SpecialKind)
from aexpy.models.difference import DiffEntry

from ..checkers import DiffRule, DiffRuleCollection, diffrule, fortype


def add(a: "ApiEntry | None", b: "ApiEntry | None", **kwargs):
    if a is None and b is not None:
        return [DiffEntry(message=f"Add {b.__class__.__name__.removesuffix('Entry').lower()} ({b.id.rsplit('.', 1)[0]}): {b.name}.")]
    return []


def remove(a: "ApiEntry | None", b: "ApiEntry | None", old: "ApiDescription", new: "ApiDescription"):
    if a is not None and b is None:
        if isinstance(a, ItemEntry):
            par = old.entries.get(a.parent)
            if isinstance(par, ClassEntry):
                # ignore sub-class overidden method removing
                for mro in par.mro:
                    base = old.entries.get(mro)
                    if isinstance(base, ClassEntry):
                        if a.name in base.members:
                            return []
        return [DiffEntry(message=f"Remove {a.__class__.__name__.removesuffix('Entry').lower()} ({a.id.rsplit('.', 1)[0]}): {a.name}.")]
    return []
