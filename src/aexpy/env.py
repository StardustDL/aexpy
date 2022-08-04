
import dataclasses
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from importlib import import_module
import os
from pathlib import Path
from re import L
from typing import TYPE_CHECKING, Any

from aexpy import getWorkingDirectory, initializeLogging, setCacheDirectory

if TYPE_CHECKING:
    from aexpy.pipelines import Pipeline
    from aexpy.producer import Producer, ProducerOptions

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

    id: "str" = ""
    """The id of the producer."""

    cache: "str | None" = None
    """The cache directory for the producer (relative path will be resolved under current cache directory)."""

    options: "ProducerOptions | None" = None

    @classmethod
    def load(cls, data: "dict") -> "ProducerConfig":
        """Loads the configuration from a dictionary."""

        if "options" in data and data["options"] is not None:
            data["options"] = ProducerOptions(**data["options"])

        return cls(**data)

    def build(self, cacheRoot: "Path | None" = None) -> "Producer":
        """Builds the producer."""

        logger.info(f"Building producer {self.id}")

        module, cls = self.id.rsplit(".", 1)
        module = import_module(module)
        cls = getattr(module, cls)
        cache = cacheRoot / self.cache if cacheRoot is not None and self.cache is not None else None
        ret = cls(cache=cache, options=self.options)
        return ret

    def match(self, producer: "Producer") -> "bool":
        """Check if the producer matches the configuration."""

        return producer.id() == self.id

    @classmethod
    def fromProducer(cls, producerCls) -> "ProducerConfig":
        """Builds a configuration from a producer class."""

        return cls(id=producerCls.id())


@dataclass
class PipelineConfig:
    """Configuration for Pipeline."""

    name: "str" = "default"
    """The name of the pipeline."""

    preprocess: "str" = ""
    """The preprocess producer config."""

    extractor: "str" = ""
    """The extractor producer config."""

    differ: "str" = ""
    """The differ producer config."""

    evaluator: "str" = ""
    """The evaluator producer config."""

    reporter: "str" = ""
    """The reporter producer config."""

    batcher: "str" = ""
    """The batcher producer config."""

    options: "ProducerOptions | None" = None

    @classmethod
    def load(cls, data: "dict") -> "PipelineConfig":
        """Loads the configuration from a dictionary."""

        if "options" in data and data["options"] is not None:
            data["options"] = ProducerOptions(**data["options"])

        return cls(**data)


@dataclass
class Configuration:
    """Configuration."""

    pipelines: "dict[str, PipelineConfig]" = field(default_factory=dict)
    producers: "dict[str, ProducerConfig]" = field(default_factory=dict)

    options: "ProducerOptions | None" = None

    interact: "bool" = False
    provider: "str" = "default"
    cache: "Path" = field(default_factory=lambda: (
        getWorkingDirectory() / "cache").resolve())
    verbose: "int" = 0

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

        if "options" in data and data["options"] is not None:
            data["options"] = ProducerOptions(**data["options"])
        else:
            data["options"] = ProducerOptions()

        return cls(**data)

    def reset(self, config: "Configuration"):
        self.interact = config.interact
        self.provider = config.provider
        self.pipelines = config.pipelines
        self.producers = config.producers
        self.verbose = config.verbose
        self.cache = config.cache
        self.options = config.options

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

    def build(self, name: "str" = "") -> "Pipeline":
        pipelines = setDefaultPipelineConfig(self.pipelines.copy())

        if name not in pipelines:
            name = self.provider

        config = pipelines[name]

        from aexpy.pipelines import Pipeline, ProducerOptions

        def buildProducer(id: "str" = "") -> "Producer | None":
            if not id:
                return None
            if id in self.producers:
                return self.producers[id].build(self.cache)
            return ProducerConfig(id=id).build(self.cache)

        options = config.options or ProducerOptions()

        return Pipeline(
            name=config.name,
            preprocessor=buildProducer(config.preprocess),
            extractor=buildProducer(config.extractor),
            differ=buildProducer(config.differ),
            evaluator=buildProducer(config.evaluator),
            reporter=buildProducer(config.reporter),
            batcher=buildProducer(config.batcher),
            options=options.replace(self.options)
        )


env = Configuration()

_pipeline: "Pipeline | None" = None


def getPipeline():
    """Get the pipeline based on the current environment."""

    global _pipeline
    if _pipeline is None:
        _pipeline = env.build()
    return _pipeline
