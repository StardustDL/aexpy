import functools
import inspect
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable, cast, override

from ...models import (ApiDescription, ApiDifference, Distribution,
                       PairProduct, Product, Report, SingleProduct)

type CounterType[T, R: (float, dict[str, float], float | dict[str, float])] = Callable[
    [T], R
]


class Statistician[T](ABC):
    def __init__(self):
        self.data: dict[str, dict[str, float | dict[str, float]]] = defaultdict(dict)
        self.counters: list[CounterType[T, float | dict[str, float]]] = []

    def renew(
        self, defaults: dict[str, dict[str, float | dict[str, float]]] | None = None
    ):
        new = self.__class__()
        new.counters = [new.count(inspect.unwrap(c)) for c in self.counters]
        new.data = defaultdict(dict)
        if defaults:
            new.data.update(defaults)
        return new

    @abstractmethod
    def id(self, data: T) -> str:
        pass

    def count[R: (float, dict[str, float])](self, func: CounterType[T, R]):
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

    def collect(self, data: Iterable[T]):
        for item in data:
            for counter in self.counters:
                counter(item)

    def keys(self):
        return (c.__name__ for c in self.counters)

    def values(self, key: str):
        for data in self.data.values():
            value = data.get(key, None)
            if value is not None:
                yield value


class SingleProductStatistician[T: SingleProduct](Statistician[T]):
    @override
    def id(self, data):
        return str(data.single())


class PairProductStatistician[T: PairProduct](Statistician[T]):
    @override
    def id(self, data):
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
        self, type: type[T], stat: Statistician[T], target: Path, redo: bool = False
    ) -> None:
        self.type = type
        self.target = target

        if redo:
            self.stat = stat.renew()
        else:
            try:
                self.stat = stat.renew(json.loads(self.target.read_text()))
            except Exception:
                self.stat = stat.renew()

    def save(self):
        self.target.write_text(json.dumps(self.stat.data))

    def process(self, files: Iterable[Path | T]):
        from ...io import load

        def loading():
            for file in files:
                if isinstance(file, Path):
                    try:
                        yield load(file, self.type)
                    except Exception:
                        pass
                else:
                    yield file

        self.stat.collect(loading())
        return self
