
import dataclasses
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from importlib import import_module
import os
from pathlib import Path
from re import L
from typing import TYPE_CHECKING, Any

from aexpy import getWorkingDirectory, initializeLogging
from aexpy.services import ProduceMode, ServiceProvider

if TYPE_CHECKING:
    from aexpy.pipelines import Pipeline
    from aexpy.producers import Producer, ProducerOptions

logger = logging.getLogger("env")


def setDefaultPipelineConfig(pipelines: "dict[str,PipelineConfig] | None" = None):
    pipelines = pipelines or {}

    pipelines.setdefault("default", PipelineConfig(name="default"))

    from aexpy.extracting.types import TypeExtractor
    pipelines.setdefault("types", PipelineConfig(
        name="types", extractor=TypeExtractor.id()))

    from aexpy.extracting.kwargs import KwargsExtractor
    pipelines.setdefault("kwargs", PipelineConfig(
        name="kwargs", extractor=KwargsExtractor.id()))

    from aexpy.extracting.attributes import AttributeExtractor
    pipelines.setdefault("attributes", PipelineConfig(
        name="attributes", extractor=AttributeExtractor.id()))

    from aexpy.extracting.base import Extractor as BaseExtractor
    from aexpy.evaluating.default import Evaluator as DefaultEvaluator
    pipelines.setdefault("base", PipelineConfig(
        name="base", extractor=BaseExtractor.id(), evaluator=DefaultEvaluator.id()))

    if os.getenv("THIRD_PARTY"):
        from aexpy.extracting.third.pycg import Extractor as PycgExtractor
        pipelines.setdefault("pycg", PipelineConfig(
            name="pycg", extractor=PycgExtractor.id()))

        from aexpy.third.pidiff.pipeline import getDefault as getPidiffDefault
        pipelines.setdefault("pidiff", getPidiffDefault())

        from aexpy.third.pycompat.pipeline import getDefault as getPycompatDefault
        pipelines.setdefault("pycompat", getPycompatDefault())

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

    def build(self) -> "Producer":
        """Builds the producer."""

        logger.info(f"Building producer {self.name} ({self.cls})")

        module, cls = self.cls.rsplit(".", 1)
        module = import_module(module)
        cls = getattr(module, cls)
        ret: "Producer" = cls()
        ret.options.load(self.options)
        return ret


@dataclass
class PipelineConfig:
    """Configuration for Pipeline."""

    name: "str" = "default"
    """The name of the pipeline."""

    preprocess: "str" = ""
    """The preprocess producer name."""

    extractor: "str" = ""
    """The extractor producer name."""

    differ: "str" = ""
    """The differ producer name."""

    reporter: "str" = ""
    """The reporter producer name."""

    batcher: "str" = ""
    """The batcher producer name."""

    @classmethod
    def load(cls, data: "dict") -> "PipelineConfig":
        """Loads the configuration from a dictionary."""
        return cls(**data)


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
        getWorkingDirectory() / "cache"))
    mode: "ProduceMode" = ProduceMode.Access

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

        self.services = ServiceProvider(self.cache)

    def build(self, name: "str" = "") -> "Pipeline":
        pipelines = setDefaultPipelineConfig(self.pipelines.copy())

        if name not in pipelines:
            name = self.pipeline

        config = pipelines[name]

        from aexpy.pipelines import Pipeline

        def buildProducer(pname: "str" = "") -> "Producer | None":
            producer = self.services.getProducer(pname)
            if producer is None and pname in self.producers:
                producer = self.producers[pname].build()
                self.services.register(producer)
            return producer

        return Pipeline(
            name=config.name,
            preprocessor=buildProducer(config.preprocess),
            extractor=buildProducer(config.extractor),
            differ=buildProducer(config.differ),
            reporter=buildProducer(config.reporter),
            batcher=buildProducer(config.batcher),
        )


env = Configuration()

_pipeline: "Pipeline | None" = None


def getPipeline():
    """Get the pipeline based on the current environment."""

    global _pipeline
    if _pipeline is None:
        _pipeline = env.build()
    return _pipeline
