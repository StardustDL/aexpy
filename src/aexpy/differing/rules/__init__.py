
import functools
import itertools
from itertools import zip_longest
from typing import Callable, OrderedDict

from aexpy.models.description import (ApiEntry, AttributeEntry, ClassEntry,
                                      CollectionEntry, FunctionEntry, ModuleEntry,
                                      Parameter, ParameterKind, SpecialEntry, SpecialKind)

from ..checkers import (DiffRule, DiffRuleCollection,
                        RuleCheckResult, diffrule, fortype)


def add(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if a is None and b is not None:
        return RuleCheckResult(True, f"Add {b.__class__.__name__.removesuffix('Entry')}: {b.id}.")
    return False


def remove(a: ApiEntry | None, b: ApiEntry | None, **kwargs):
    if a is not None and b is None:
        return RuleCheckResult(True, f"Remove {a.__class__.__name__.removesuffix('Entry').lower()}: {a.id}.")
    return False
