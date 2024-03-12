from logging import Logger
from typing import override

from ..environments import ExecutionEnvironment
from ..models import ApiDescription, Distribution
from ..producers import ProduceContext, produce
from ..utils import getObjectId
from . import Extractor
from .third.mypyserver import PackageMypyServer


class DefaultExtractor(Extractor):
    """Basic extractor that uses dynamic inspect."""

    def __init__(
        self, /, logger: Logger | None = None, env: ExecutionEnvironment | None = None
    ):
        super().__init__(logger=logger)
        self.env = env

    def base(self, /, dist: Distribution, context: ProduceContext[ApiDescription]):
        from .base import BaseExtractor

        with context.using(BaseExtractor(env=self.env)) as producer:
            producer.extract(dist, context.product)
        context.product.distribution = dist

    def attributes(
        self,
        /,
        dist: Distribution,
        context: ProduceContext[ApiDescription],
        server: PackageMypyServer | None,
    ):
        from .attributes import AttributeExtractor

        with context.using(
            AttributeExtractor(serverProvider=lambda _: server)
        ) as producer:
            producer.extract(dist, context.product)

    def kwargs(
        self,
        /,
        dist: Distribution,
        context: ProduceContext[ApiDescription],
        server: PackageMypyServer | None,
    ):
        from .kwargs import KwargsExtractor

        with context.using(
            KwargsExtractor(serverProvider=lambda _: server)
        ) as producer:
            producer.extract(dist, context.product)

    def types(
        self,
        /,
        dist: Distribution,
        context: ProduceContext[ApiDescription],
        server: PackageMypyServer | None,
    ):
        from .types import TypeExtractor

        with context.using(TypeExtractor(serverProvider=lambda _: server)) as producer:
            producer.extract(dist, context.product)

    @override
    def extract(self, /, dist, product):
        with produce(product, self.logger, raising=True) as context:
            self.base(dist, context)

            assert dist.rootPath

            try:
                server = PackageMypyServer(dist.rootPath, dist.src, self.logger)
                server.prepare()
            except Exception:
                self.logger.error(
                    f"Failed to run mypy server at {dist.rootPath}: {dist.src}.",
                    exc_info=True,
                )
                server = None

            self.attributes(dist, context, server)
            self.kwargs(dist, context, server)
            self.types(dist, context, server)

            self.name = context.combinedProducers(self)
