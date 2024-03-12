from contextlib import contextmanager
from logging import Logger

from .. import __version__, getShortCommitId
from ..diffing import Differ
from ..environments import ExecutionEnvironment, ExecutionEnvironmentBuilder
from ..extracting import Extractor
from ..models import (ApiDescription, ApiDifference, Distribution, Product,
                      Report)
from ..preprocessing import Preprocessor
from ..producers import ProduceContext, produce
from ..reporting import Reporter
from ..tools.stats import StatisticianWorker


class ServiceProvider:
    def __init__(self, name: str | None = None) -> None:
        self.name = name or f"aexpy@{__version__}-{getShortCommitId()}"

    def environmentBuilder(
        self, /, logger: Logger | None = None
    ) -> ExecutionEnvironmentBuilder:
        from ..extracting.environment import getExtractorEnvironmentBuilder

        return getExtractorEnvironmentBuilder(logger=logger)

    def preprocessor(self, /, logger: Logger | None = None) -> Preprocessor:
        from ..preprocessing.counter import FileCounterPreprocessor

        return FileCounterPreprocessor(logger=logger)

    def extractor(
        self, /, logger: Logger | None = None, env: ExecutionEnvironment | None = None
    ) -> Extractor:
        from ..extracting.default import DefaultExtractor

        return DefaultExtractor(logger=logger, env=env)

    def differ(self, /, logger: Logger | None = None) -> Differ:
        from ..diffing.default import DefaultDiffer

        return DefaultDiffer(logger=logger)

    def reporter(self, /, logger: Logger | None = None) -> Reporter:
        from ..reporting.text import TextReporter

        return TextReporter(logger=logger)

    def statistician(self, /, logger: Logger | None = None) -> StatisticianWorker:
        return StatisticianWorker(logger=logger)

    @contextmanager
    def produce[
        T: Product
    ](
        self,
        product: T,
        logger: Logger | None = None,
        context: ProduceContext[T] | None = None,
    ):
        if context:
            yield context
        else:
            with produce(product, logger=logger, service=self.name) as context:
                yield context

    def preprocess(
        self,
        /,
        product: Distribution,
        *,
        logger: Logger | None = None,
        context: ProduceContext[Distribution] | None = None,
    ):
        with self.produce(product, logger=logger, context=context) as context:
            with context.using(self.preprocessor(context.logger)) as producer:
                producer.preprocess(product)
        return context

    def extract[
        E: ExecutionEnvironment
    ](
        self,
        /,
        dist: Distribution,
        *,
        logger: Logger | None = None,
        context: ProduceContext[ApiDescription] | None = None,
        envBuilder: ExecutionEnvironmentBuilder[E] | None = None,
    ):
        with self.produce(
            ApiDescription(distribution=dist), logger=logger, context=context
        ) as context:
            envBuilder = envBuilder or self.environmentBuilder(context.logger)

            with envBuilder.use(pyversion=dist.pyversion, logger=context.logger) as env:
                with context.using(self.extractor(context.logger, env=env)) as producer:
                    producer.extract(dist, context.product)
        return context

    def diff(
        self,
        /,
        old: ApiDescription,
        new: ApiDescription,
        *,
        logger: Logger | None = None,
        context: ProduceContext[ApiDifference] | None = None,
    ):
        with self.produce(
            ApiDifference(old=old.distribution, new=new.distribution),
            logger=logger,
            context=context,
        ) as context:
            with context.using(self.differ(context.logger)) as producer:
                producer.diff(old, new, context.product)
        return context

    def report(
        self,
        /,
        diff: ApiDifference,
        *,
        logger: Logger | None = None,
        context: ProduceContext[Report] | None = None,
    ):
        with self.produce(
            Report(old=diff.old, new=diff.new),
            logger=logger,
            context=context,
        ) as context:
            with context.using(self.reporter(context.logger)) as producer:
                producer.report(diff, context.product)
        return context


def getService():
    return ServiceProvider()


def loadServiceFromCode(src: str):
    from hashlib import sha256
    from importlib.util import module_from_spec, spec_from_loader

    spec = spec_from_loader(sha256(src.encode()).hexdigest(), loader=None)
    assert spec is not None, "Failed to create module spec."
    mod = module_from_spec(spec)

    srcCode = compile(src, "<memory>", "exec")

    exec("from aexpy.services import *", mod.__dict__)
    exec(srcCode, mod.__dict__)

    getter = getattr(mod, "getService", None)
    assert callable(getter), "Failed to get valid `getService` getter."

    service = getter()
    assert isinstance(
        service, ServiceProvider
    ), f"Failed to get valid service instance: got {type(service)}."

    return service
