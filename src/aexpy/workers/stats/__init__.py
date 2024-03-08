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
from ...models import (ApiDescription, ApiDifference, Distribution,
                       PairProduct, Product, Report, SingleProduct)

type CounterType[T, R: (float, dict[str, float], float | dict[str, float])] = Callable[
    [T], R
]


class Statistician[T](ABC):
    def __init__(self, /):
        self.data: dict[str, dict[str, float | dict[str, float]]] = defaultdict(dict)
        self.counters: list[CounterType[T, float | dict[str, float]]] = []

    def renew(
        self, /, defaults: dict[str, dict[str, float | dict[str, float]]] | None = None
    ):
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

    def collect(self, /, data: Iterable[T]):
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


class StatisticianWorker[T: Product]:
    def __init__(
        self,
        /,
        type: type[T],
        stat: Statistician[T],
        target: Path,
        load: bool = False,
        logger: Logger | None = None,
    ) -> None:
        self.type = type
        self.target = target
        self.logger = logger or logging.getLogger()
        self.stat = stat.renew()

        if load:
            self.load()

    def load(self, /):
        try:
            self.stat = self.stat.renew(json.loads(self.target.read_text()))
        except Exception as ex:
            raise Exception(f"Failed to load stats from {self.target}: {ex}") from ex

    def save(self, /):
        self.target.write_text(json.dumps(self.stat.data))

    def process(self, /, sources: Iterable[LoadSourceType | T]):
        def loading():
            for source in sources:
                if isinstance(source, self.type):
                    yield source
                else:
                    try:
                        yield load(source, self.type)
                    except Exception:
                        self.logger.error(
                            f"Failed to load from {source}", exc_info=True
                        )

        self.stat.collect(loading())
        return self
