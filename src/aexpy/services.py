from logging import Logger
from .environments import ExecutionEnvironmentBuilder, ExecutionEnvironment
from .preprocessing import Preprocessor
from .extracting import Extractor
from .diffing import Differ
from .reporting import Reporter
from . import __version__, getCommitId


class ServiceProvider:
    def __init__(self, name: str | None = None) -> None:
        self.name = (
            name
            or f"aexpy@{__version__}{'-' + getCommitId()[-7:] if getCommitId() else ''}"
        )

    def environmentBuilder(
        self, /, logger: Logger | None = None
    ) -> ExecutionEnvironmentBuilder:
        from .extracting.environment import getExtractorEnvironmentBuilder

        return getExtractorEnvironmentBuilder(logger=logger)

    def preprocessor(self, /, logger: Logger | None = None) -> Preprocessor:
        from .preprocessing.counter import FileCounterPreprocessor

        return FileCounterPreprocessor(logger=logger)

    def extractor(
        self, /, logger: Logger | None = None, env: ExecutionEnvironment | None = None
    ) -> Extractor:
        from .extracting.default import DefaultExtractor

        return DefaultExtractor(logger=logger, env=env)

    def differ(self, /, logger: Logger | None = None) -> Differ:
        from .diffing.default import DefaultDiffer

        return DefaultDiffer(logger=logger)

    def reporter(self, /, logger: Logger | None = None) -> Reporter:
        from .reporting.text import TextReporter

        return TextReporter(logger=logger)


def getService():
    return ServiceProvider()


def loadServiceFromCode(src: str):
    from importlib.util import spec_from_loader, module_from_spec
    from hashlib import sha256

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
