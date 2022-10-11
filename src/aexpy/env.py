
import dataclasses
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from importlib import import_module
import os
from pathlib import Path
from re import L
from typing import TYPE_CHECKING, Any, Type

from aexpy import getWorkingDirectory, initializeLogging
from aexpy.caching.filesystem import FileProduceCacheManager
from aexpy.models import ProduceMode
from aexpy.services import ServiceProvider
from aexpy.producers import Producer
from aexpy.pipelines import Pipeline, PipelineConfig

logger = logging.getLogger("env")


def defaultProducerConfig():
    producers: "dict[str, ProducerConfig]" = {}

    def add(config: "ProducerConfig"):
        producers[config.name] = config

    from aexpy.preprocessing.basic import BasicPreprocessor
    add(ProducerConfig.fromProducer(
        BasicPreprocessor, "pre", {"mirror": True}))

    from aexpy.preprocessing.pip import PipPreprocessor
    add(ProducerConfig.fromProducer(
        PipPreprocessor, "pip", {"mirror": True}))

    from aexpy.extracting.types import TypeExtractor
    add(ProducerConfig.fromProducer(TypeExtractor, "types"))

    from aexpy.extracting.kwargs import KwargsExtractor
    add(ProducerConfig.fromProducer(KwargsExtractor, "kwargs"))

    from aexpy.extracting.attributes import AttributeExtractor
    add(ProducerConfig.fromProducer(AttributeExtractor, "attrs"))

    from aexpy.extracting.base import BaseExtractor
    add(ProducerConfig.fromProducer(BaseExtractor, "base"))

    from aexpy.diffing.differs.default import DefaultDiffer
    add(ProducerConfig.fromProducer(DefaultDiffer, "diff"))

    from aexpy.diffing.evaluators.default import DefaultEvaluator
    add(ProducerConfig.fromProducer(DefaultEvaluator, "eval"))

    from aexpy.diffing.verifiers.default import DefaultVerifier
    add(ProducerConfig.fromProducer(DefaultVerifier, "verify"))

    from aexpy.reporting.text import TextReporter
    add(ProducerConfig.fromProducer(TextReporter, "text"))

    from aexpy.batching import InProcessBatcher
    add(ProducerConfig.fromProducer(InProcessBatcher, "inprocess"))

    from aexpy.services import DemoService
    add(ProducerConfig.fromProducer(DemoService, "demo"))

    if os.getenv("THIRD_PARTY"):
        from aexpy.extracting.third.pycg import PycgExtractor
        add(ProducerConfig.fromProducer(PycgExtractor, "pycg"))

        from aexpy.third.pidiff.service import PidiffService
        add(ProducerConfig.fromProducer(PidiffService, "pidiff"))

        from aexpy.third.pycompat.service import PycompatService
        add(ProducerConfig.fromProducer(PycompatService, "pycompat"))

    return producers


def setDefaultPipelineConfig(pipelines: "dict[str,PipelineConfig] | None" = None):
    pipelines = pipelines or {}

    defaultConfig = PipelineConfig(
        name="default",
        preprocessor="pip",
        extractor="types",
        differ="verify",
        reporter="text",
        batcher="inprocess")

    pipelines.setdefault("default", defaultConfig)

    pipelines.setdefault("demo",
                         PipelineConfig(name="demo",
                                        preprocessor="demo",
                                        extractor="demo",
                                        differ="demo",
                                        reporter="demo",
                                        batcher="demo"))

    pipelines.setdefault("base", dataclasses.replace(
        defaultConfig, name="base", extractor="base"))
    pipelines.setdefault("attrs", dataclasses.replace(
        defaultConfig, name="attrs", extractor="attrs"))
    pipelines.setdefault("kwargs", dataclasses.replace(
        defaultConfig, name="kwargs", extractor="kwargs"))
    pipelines.setdefault("types", dataclasses.replace(
        defaultConfig, name="types", extractor="types"))

    pipelines.setdefault("diff", dataclasses.replace(
        defaultConfig, name="diff", differ="diff"))
    pipelines.setdefault("eval", dataclasses.replace(
        defaultConfig, name="eval", differ="eval"))
    pipelines.setdefault("verify", dataclasses.replace(
        defaultConfig, name="verify", differ="verify"))

    if os.getenv("THIRD_PARTY"):
        pipelines.setdefault("pycg", dataclasses.replace(
            defaultConfig, name="pycg", extractor="pycg"))

        pipelines.setdefault("pidiff", PipelineConfig(
            name="pidiff",
            preprocessor="pip",
            differ="pidiff",
            reporter="pidiff",
            batcher="pidiff"))

        pipelines.setdefault("pycompat", PipelineConfig(
            name="pycompat",
            preprocessor="pip",
            extractor="pycompat",
            differ="pycompat",
            reporter="pycompat",
            batcher="pycompat"))

    return pipelines


@dataclass
class ProducerConfig:
    """Configuration for Producer."""

    cls: "str" = ""
    """The class of the producer."""

    name: "str" = ""
    """The name of the producer."""

    options: "dict" = field(default_factory=dict)
    """The options for the producer."""

    @classmethod
    def load(cls, data: "dict") -> "ProducerConfig":
        """Loads the configuration from a dictionary."""

        return cls(**data)

    @classmethod
    def fromProducer(cls, producer: "Type[Producer] | Producer", name: "str", options: "dict | None" = None) -> "ProducerConfig":
        """Creates a configuration from a producer."""

        if isinstance(producer, Producer):
            producer = producer.__class__

        return cls(cls=producer.cls(), name=name, options=options or {})

    def build(self) -> "Producer":
        """Builds the producer."""

        logger.info(f"Building producer {self.name} ({self.cls})")

        module, cls = self.cls.rsplit(".", 1)
        module = import_module(module)
        cls = getattr(module, cls)
        ret: "Producer" = cls()
        ret.name = self.name
        ret.options.load(self.options)
        return ret


@dataclass
class Configuration:
    """Configuration."""

    pipelines: "dict[str, PipelineConfig]" = field(default_factory=dict)
    producers: "dict[str, ProducerConfig]" = field(default_factory=dict)

    interact: "bool" = False
    pipeline: "str" = "default"
    cache: "Path" = field(default_factory=lambda: (
        getWorkingDirectory() / "cache").resolve())
    verbose: "int" = 0
    services: "ServiceProvider" = field(default_factory=lambda: ServiceProvider(
        FileProduceCacheManager(getWorkingDirectory() / "cache")))

    @classmethod
    def load(cls, data: "dict") -> "Configuration":
        """Loads the configuration from a dictionary."""
        if "pipelines" in data and data["pipelines"] is not None:
            data["pipelines"] = {
                k: dataclasses.replace(PipelineConfig.load(v), name=k) for k, v in data["pipelines"].items()
            }

        if "producers" in data and data["producers"] is not None:
            data["producers"] = {
                k: dataclasses.replace(ProducerConfig.load(v), id=k) for k, v in data["producers"].items()
            }

        if "cache" in data and data["cache"] is not None:
            data["cache"] = Path(data["cache"])

        if "mode" in data and data["mode"] is not None:
            data["mode"] = ProduceMode(data["mode"])

        return cls(**data)

    def reset(self, config: "Configuration"):
        self.interact = config.interact
        self.pipeline = config.pipeline
        self.pipelines = config.pipelines
        self.producers = config.producers
        self.verbose = config.verbose
        self.cache = config.cache

    def prepare(self):
        loggingLevel = {
            0: logging.CRITICAL,
            1: logging.ERROR,
            2: logging.WARNING,
            3: logging.INFO,
            4: logging.DEBUG,
            5: logging.NOTSET
        }[self.verbose]

        initializeLogging(loggingLevel)

        self.services = ServiceProvider(FileProduceCacheManager(self.cache))

        for producer in self.producers.values():
            self.services.register(producer.build())

        for producer in defaultProducerConfig().values():
            if self.services.getProducer(producer.name) is None:
                self.services.register(producer.build())

    def build(self, name: "str" = "") -> "Pipeline":
        pipelines = setDefaultPipelineConfig(self.pipelines.copy())

        if name not in pipelines:
            name = self.pipeline

        config = pipelines[name]

        return self.services.build(config)


env = Configuration()

_pipeline: "Pipeline | None" = None


def getPipeline():
    """Get the pipeline based on the current environment."""

    global _pipeline
    if _pipeline is None:
        _pipeline = env.build()
    return _pipeline
