
from dataclasses import dataclass
from importlib import import_module
import logging
from pathlib import Path
from re import L
from typing import Any, TYPE_CHECKING

from dataclasses import field

from aexpy import initializeLogging, setCacheDirectory

if TYPE_CHECKING:
    from aexpy.producer import Producer
    from aexpy.pipelines import Pipeline

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


@dataclass
class Options:
    interact: "bool" = False
    provider: "PipelineConfig | None" = None
    config: "dict[str, ProducerConfig]" = field(default_factory=dict)
    cache: "Path | None" = None
    verbose: "int" = 0
    redo: "bool | None" = None
    cached: "bool | None" = None

    def reset(self, options: "Options"):
        self.interact = options.interact
        self.provider = options.provider
        self.config = options.config
        self.redo = options.redo
        self.cached = options.cached
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

        if self.cache:
            setCacheDirectory(self.cache)

    def loadConfig(self, data: "dict[str, Any]"):
        """Loads the configuration from a dictionary."""

        for key, value in data:
            config = ProducerConfig(**value)
            if not config.id:
                config.id = key
            self.config[key] = config

    def loadProvider(self, data: "dict[str, Any]"):
        """Loads the provider configuration from a dictionary, every entry will also be registered as a config."""

        for key, value in data:
            if not value:
                continue
            data[key] = ProducerConfig(**value)
            self.config[key] = data[key]
        self.provider = PipelineConfig(**data)

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

    from aexpy.pipelines import Pipeline

    global _pipeline
    if _pipeline is None:
        provider = env.provider or PipelineConfig()
        _pipeline = Pipeline(
            preprocessor=provider.preprocess.build() if provider.preprocess else None,
            extractor=provider.extractor.build() if provider.extractor else None,
            differ=provider.differ.build() if provider.differ else None,
            evaluator=provider.evaluator.build() if provider.evaluator else None,
            reporter=provider.reporter.build() if provider.reporter else None,
            redo=env.redo, cached=env.cached
        )
    return _pipeline
