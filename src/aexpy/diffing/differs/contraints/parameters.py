import functools
import itertools
from itertools import zip_longest
from typing import Callable, Iterable, Iterator

from ....models import ApiDescription
from ....models.description import FunctionEntry, Parameter, ParameterKind
from ....models.difference import DiffEntry
from ..checkers import DiffConstraintCollection, typedCons

ParameterConstraints = DiffConstraintCollection()


def matchParameters(a: FunctionEntry, b: FunctionEntry):
    def inner() -> Iterator[tuple[Parameter | None, Parameter | None]]:
        for x, y in zip_longest(a.positionalOnlys, b.positionalOnlys):
            if x is None:
                ty: Parameter = y
                if ty.isKeyword:  # new parameter to pair with keyword parameter
                    continue
            yield x, y

        for x in a.positionals:
            if x.isKeyword:
                y = b.getParameter(x.name)
                if y is None or not y.isPositional:
                    yield x, None

        kwA = {v.name: v for v in a.keywords}
        kwB = {v.name: v for v in b.keywords}

        for k, v in kwA.items():
            yield v, kwB.get(k)

        for k, v in kwB.items():
            if k not in kwA:
                yield None, v

        x, y = a.varPositional, b.varPositional
        if x or y:
            yield x, y

        x, y = a.varKeyword, b.varKeyword
        if x or y:
            yield x, y

    done = set()

    for x, y in inner():
        nx = x.name if x else None
        ny = y.name if y else None
        if (nx, ny) in done:
            continue
        done.add((nx, ny))
        yield x, y


def changeParameter(
    checker: Callable[
        [Parameter | None, Parameter | None, FunctionEntry, FunctionEntry],
        Iterable[DiffEntry],
    ],
):
    @typedCons(FunctionEntry)
    @functools.wraps(checker)
    def wrapper(
        a: FunctionEntry, b: FunctionEntry, old: ApiDescription, new: ApiDescription
    ):
        for x, y in matchParameters(a, b):
            for item in checker(x, y, a, b):
                item.data["old"] = x.name if x else ""
                item.data["new"] = y.name if y else ""
                yield item

    return wrapper


@ParameterConstraints.cons
@changeParameter
def AddParameter(
    a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry
):
    if a is None and b is not None:
        yield DiffEntry(
            message=f"Add {b.kind.name} parameter ({old.id}): {b.name}{f' (from {b.source})' if b.source and b.source != new.id else ''}."
        )


@ParameterConstraints.cons
@changeParameter
def RemoveParameter(
    a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry
):
    if a is not None and b is None:
        yield DiffEntry(
            message=f"Remove {a.kind.name} parameter ({old.id}): {a.name}{f' (from {a.source})' if a.source and a.source != old.id else ''}."
        )


@ParameterConstraints.cons
@changeParameter
def ChangeParameterOptional(
    a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry
):
    if a is not None and b is not None and a.optional != b.optional:
        if a.name == b.name:
            yield DiffEntry(
                message=f"Switch parameter optional ({old.id}): {a.name}: {a.optional} -> {b.optional}.",
                data={"oldoptional": a.optional, "newoptional": b.optional},
            )


@ParameterConstraints.cons
@changeParameter
def ChangeParameterDefault(
    a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry
):
    if (
        a is not None
        and b is not None
        and a.optional
        and b.optional
        and a.default != b.default
    ):
        if a.name == b.name:
            yield DiffEntry(
                message=f"Change parameter default ({old.id}): {a.name}: {a.default} -> {b.default}.",
                data={"olddefault": a.default, "newdefault": b.default},
            )


@ParameterConstraints.cons
@typedCons(FunctionEntry)
def MoveParameter(
    a: FunctionEntry, b: FunctionEntry, old: "ApiDescription", new: "ApiDescription"
):
    pa = [p.name for p in a.positionals]
    pb = [p.name for p in b.positionals]
    shared = set(pa) & set(pb)
    changed: "dict[str, tuple[int,int]]" = {}
    for item in shared:
        i = pa.index(item)
        j = pb.index(item)
        if i != j:
            changed[item] = i, j
    return (
        DiffEntry(
            message=f"Move parameter ({a.id}): {k}: {i+1} -> {j+1}.",
            data={"name": k, "oldindex": i, "newindex": j},
        )
        for k, (i, j) in changed.items()
    )
