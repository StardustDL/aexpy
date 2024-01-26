import subprocess
from logging import Logger

from aexpy import json
from aexpy import getPythonExe
from aexpy.environments import ExecutionEnvironment
from aexpy.extracting.enriching.callgraph import Callgraph
from aexpy.extracting.third.mypyserver import PackageMypyServer
from aexpy.models.description import TRANSFER_BEGIN, FunctionEntry

from .. import getAppDirectory
from ..models import ApiDescription, Distribution
from . import Extractor


class DefaultExtractor[E: ExecutionEnvironment](Extractor):
    """Basic extractor that uses dynamic inspect."""

    def __init__(self, env: type[E] | None = None, logger: Logger | None = None):
        super().__init__(logger=logger)
        from ..environments import CurrentEnvironment
        self.env = env or CurrentEnvironment

    def base(self, dist: Distribution, product: ApiDescription):
        from .base import BaseExtractor
        BaseExtractor(self.logger, self.env).extract(dist, product)
        product.distribution = dist

    def attributes(
        self,
        dist: Distribution,
        product: ApiDescription,
        server: PackageMypyServer | None,
    ):
        from .attributes import AttributeExtractor
        AttributeExtractor(self.logger, lambda _: server).extract(dist, product)

    def kwargs(
        self,
        dist: Distribution,
        product: ApiDescription,
        server: PackageMypyServer | None,
    ):
        from .kwargs import KwargsExtractor
        KwargsExtractor(self.logger, lambda _: server).extract(dist, product)

    def types(
        self,
        dist: Distribution,
        product: ApiDescription,
        server: PackageMypyServer | None,
    ):
        from .types import TypeExtractor
        TypeExtractor(self.logger, lambda _: server).extract(dist, product)

    def extract(self, dist: Distribution, product: ApiDescription):
        self.base(dist, product)

        assert dist.rootPath

        try:
            server = PackageMypyServer(dist.rootPath, dist.src, self.logger)
            server.prepare()
        except Exception as ex:
            self.logger.error(
                f"Failed to run mypy server at {dist.rootPath}: {dist.src}.",
                exc_info=ex,
            )
            server = None

        self.attributes(dist, product, server)
        self.kwargs(dist, product, server)
        self.types(dist, product, server)