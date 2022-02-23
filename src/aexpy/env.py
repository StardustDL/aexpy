
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from importlib import import_module
from pathlib import Path
from re import L
from typing import TYPE_CHECKING, Any

from aexpy import getWorkingDirectory, initializeLogging, setCacheDirectory

if TYPE_CHECKING:
    from aexpy.pipelines import Pipeline
    from aexpy.producer import Producer

logger = logging.getLogger("env")


@dataclass
class ProducerConfig:
    """Configuration for Producer."""

    id: "str" = ""
    """The id of the producer."""

    cache: "str | None" = None
    """The cache directory for the producer (relative path will be resolved under current cache directory)."""

    redo: "bool | None" = None
    """Redo producing."""

    cached: "bool | None" = None
    """Caching producing."""

    onlyCache: "bool | None" = None
    """Only load from cache."""

    def build(self) -> "Producer":
        """Builds the producer."""

        logger.info(f"Building producer {self.id}")

        module, cls = self.id.rsplit(".", 1)
        module = import_module(module)
        cls = getattr(module, cls)
        ret = cls()
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

    preprocess: "ProducerConfig | None" = None
    """The preprocess producer config."""

    extractor: "ProducerConfig | None" = None
    """The extractor producer config."""

    differ: "ProducerConfig | None" = None
    """The differ producer config."""

    evaluator: "ProducerConfig | None" = None
    """The evaluator producer config."""

    reporter: "ProducerConfig | None" = None
    """The reporter producer config."""

    batcher: "ProducerConfig | None" = None
    """The batcher producer config."""

    redo: "bool | None" = None
    cached: "bool | None" = None
    onlyCache: "bool | None" = None

    def build(self) -> "Pipeline":
        from aexpy.pipelines import Pipeline

        return Pipeline(
            name=self.name,
            preprocessor=self.preprocess.build() if self.preprocess else None,
            extractor=self.extractor.build() if self.extractor else None,
            differ=self.differ.build() if self.differ else None,
            evaluator=self.evaluator.build() if self.evaluator else None,
            reporter=self.reporter.build() if self.reporter else None,
            batcher=self.batcher.build() if self.batcher else None,
            redo=self.redo, cached=self.cached, onlyCache=self.onlyCache
        )


@dataclass
class Options:
    interact: "bool" = False
    provider: "PipelineConfig | None" = None
    config: "dict[str, ProducerConfig]" = field(default_factory=dict)
    cache: "Path" = field(default_factory=lambda: (
        getWorkingDirectory() / "cache").resolve())
    verbose: "int" = 0

    def reset(self, options: "Options"):
        self.interact = options.interact
        self.provider = options.provider
        self.config = options.config
        self.verbose = options.verbose
        self.cache = options.cache

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

    def loadConfig(self, data: "dict[str, Any]"):
        """Loads the configuration from a dictionary."""

        for key, value in data:
            config = ProducerConfig(**value)
            if not config.id:
                config.id = key
            self.config[key] = config

    def loadProvider(self, data: "dict[str, Any]"):
        """Loads the provider configuration from a dictionary, every entry will also be registered as a config."""

        name = data.pop("name") if "name" in data else ""
        name = name or "default"
        redo = data.pop("redo") if "redo" in data else None
        cached = data.pop("cached") if "cached" in data else None
        onlyCache = data.pop("onlyCache") if "onlyCache" in data else None

        for key, value in data:
            if not value:
                continue
            data[key] = ProducerConfig(**value)
            self.config[key] = data[key]
        self.provider = PipelineConfig(
            name=name, redo=redo, cached=cached, onlyCache=onlyCache, **data)

    def getConfig(self, producer: "Producer") -> "ProducerConfig | None":
        """Returns the configuration for the producer."""

        config = self.config.get(producer.id())
        if config:
            assert config.match(producer)
        return config


env = Options()

_pipeline: "Pipeline | None" = None


def getPipeline():
    """Get the pipeline based on the current environment."""

    global _pipeline
    if _pipeline is None:
        provider = env.provider or PipelineConfig()
        _pipeline = provider.build()
    return _pipeline
