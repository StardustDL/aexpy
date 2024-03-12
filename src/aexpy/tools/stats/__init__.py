import functools
import inspect
import json
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from logging import Logger
from pathlib import Path
from typing import Callable, Iterable, cast, override

from ...io import LoadSourceType, load
from ...models import (ApiDescription, ApiDifference, CoreProduct,
                       Distribution, PairProduct, Product, Report,
                       SingleProduct)
from ...producers import Producer
from ..models import StatDataType, StatSummary

type CounterType[T, R: (float, dict[str, float], float | dict[str, float])] = Callable[
    [T], R
]


class Statistician[T](ABC):
    def __init__(self, /):
        self.data: StatDataType = defaultdict(dict)
        self.counters: list[CounterType[T, float | dict[str, float]]] = []

    def renew(self, /, defaults: StatDataType | None = None):
        new = self.__class__()
        new.counters = [new.count(inspect.unwrap(c)) for c in self.counters]
        new.data = defaultdict(dict)
        if defaults:
            new.data.update(defaults)
        return new

    @abstractmethod
    def id(self, /, data: T) -> str:
        pass

    def count[R: (float, dict[str, float])](self, /, func: CounterType[T, R]):
        @functools.wraps(func)
        def wrapper(data: T) -> R:
            cached = self.data[self.id(data)]
            value = cached.get(func.__name__, None)
            if value is not None:
                return cast(R, value)
            else:
                value = func(data)
                cached[func.__name__] = value
                return value

        self.counters.append(wrapper)
        return wrapper

    def collect(self, /, *data: T):
        for item in data:
            for counter in self.counters:
                counter(item)

    def keys(self, /):
        return (c.__name__ for c in self.counters)

    def values(self, /, key: str):
        for data in self.data.values():
            value = data.get(key, None)
            if value is not None:
                yield value


class SingleProductStatistician[T: SingleProduct](Statistician[T]):
    @override
    def id(self, /, data):
        return str(data.single())


class PairProductStatistician[T: PairProduct](Statistician[T]):
    @override
    def id(self, /, data):
        return str(data.pair())


class DistStatistician(SingleProductStatistician[Distribution]):
    pass


class ApiStatistician(SingleProductStatistician[ApiDescription]):
    pass


class ChangeStatistician(PairProductStatistician[ApiDifference]):
    pass


class ReportStatistician(PairProductStatistician[Report]):
    pass


class StatisticianWorker(Producer):
    def __init__(
        self,
        /,
        logger: Logger | None = None,
        dists: Statistician[Distribution] | None = None,
        apis: Statistician[ApiDescription] | None = None,
        changes: Statistician[ApiDifference] | None = None,
        reports: Statistician[Report] | None = None,
    ):
        super().__init__(logger)
        from . import apis as Mapis
        from . import changes as Mchanges
        from . import dists as Mdists
        from . import reports as Mreports

        self.dists = (dists or Mdists.S).renew()
        self.apis = (apis or Mapis.S).renew()
        self.changes = (changes or Mchanges.S).renew()
        self.reports = (reports or Mreports.S).renew()

    def count(
        self, /, sources: Iterable[LoadSourceType | CoreProduct], product: StatSummary
    ):
        def autoLoad(source: LoadSourceType | CoreProduct):
            match source:
                case Distribution() | ApiDescription() | ApiDifference() | Report():
                    return source
                case _:
                    return load(source)

        for source in sources:
            try:
                source = autoLoad(source)
                if isinstance(source, Distribution):
                    self.dists.collect(source)
                if isinstance(source, ApiDescription):
                    self.apis.collect(source)
                if isinstance(source, ApiDifference):
                    self.changes.collect(source)
                if isinstance(source, Report):
                    self.reports.collect(source)
            except Exception:
                self.logger.error(f"Failed to collect from {source}", exc_info=True)

        product.dists.update(self.dists.data)
        product.apis.update(self.apis.data)
        product.changes.update(self.changes.data)
        product.reports.update(self.reports.data)
