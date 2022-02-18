
from dataclasses import dataclass
from importlib import import_module
import logging
from pathlib import Path
from re import L
from typing import Any, TYPE_CHECKING

from dataclasses import field

if TYPE_CHECKING:
    from aexpy.producer import Producer
    from aexpy.pipelines import Pipeline

logger = logging.getLogger("env")


@dataclass
class ProducerConfig:
    id: "str" = ""
    cache: "str | None" = None
    redo: "bool | None" = None
    cached: "bool | None" = None

    def build(self) -> "Producer":
        logger.info(f"Building producer {self.id}")

        module, cls = self.id.rsplit(".", 1)
        module = import_module(module)
        cls = getattr(module, cls)
        ret = cls()
        return ret

    def match(self, producer: "Producer") -> "bool":
        return producer.id() == self.id

    @classmethod
    def fromProducer(cls, producerCls) -> "ProducerConfig":
        return cls(id=producerCls.id())


@dataclass
class PipelineConfig:
    preprocess: "ProducerConfig | None" = None
    extractor: "ProducerConfig | None" = None
    differ: "ProducerConfig | None" = None
    evaluator: "ProducerConfig | None" = None
    reporter: "ProducerConfig | None" = None


@dataclass
class Options:
    interact: "bool" = False
    provider: "PipelineConfig | None" = None
    config: "dict[str, ProducerConfig]" = field(default_factory=dict)
    redo: "bool | None" = None
    cached: "bool | None" = None

    def reset(self, options: "Options"):
        self.interact = options.interact
        self.provider = options.provider
        self.config = options.config
        self.redo = options.redo
        self.cached = options.cached

    def loadConfig(self, data: "dict[str, Any]"):
        for key, value in data:
            config = ProducerConfig(**value)
            if not config.id:
                config.id = key
            self.config[key] = config

    def loadProvider(self, data: "dict[str, Any]"):
        for key, value in data:
            if not value:
                continue
            data[key] = ProducerConfig(**value)
            self.config[key] = data[key]
        self.provider = PipelineConfig(**data)

    def getConfig(self, producer: "Producer") -> "ProducerConfig | None":
        config = self.config.get(producer.id())
        if config:
            assert config.match(producer)
        return config


env = Options()

_pipeline: "Pipeline | None" = None


def getPipeline():
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
