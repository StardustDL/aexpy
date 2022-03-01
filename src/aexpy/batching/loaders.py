
from logging import Logger
from pathlib import Path
from aexpy.batching import Batcher, DefaultBatcher
from aexpy.env import getPipeline
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, ProjectResult, Release, ReleasePair, Report)
from aexpy.pipelines import Pipeline
from aexpy.producer import NoCachedProducer, ProducerOptions

from .generators import (diffed, evaluated, extracted, pair, preprocessed,
                         reported, single)


class BatchLoader(DefaultBatcher, NoCachedProducer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, pipeline: "Pipeline | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.pipeline = pipeline or getPipeline()

    def process(self, product: "ProjectResult", project: "str", workers: "int | None" = None, retry: "int" = 3):
        self.index(project)
        product.releases = self.releases
        product.preprocessed = self.preprocessed
        product.extracted = self.extracted
        product.pairs = self.pairs
        product.diffed = self.diffed
        product.evaluated = self.evaluated
        product.reported = self.reported

    def index(self, project: str):
        self.releases = single(project)
        self.preprocessed = list(
            filter(preprocessed(self.pipeline), self.releases))
        self.extracted = list(
            filter(extracted(self.pipeline), self.preprocessed))
        self.pairs = pair(self.extracted)
        self.diffed = list(filter(diffed(self.pipeline), self.pairs))
        self.evaluated = list(filter(evaluated(self.pipeline), self.diffed))
        self.reported = list(filter(reported(self.pipeline), self.evaluated))

    def preprocess(self, release: "Release") -> "Distribution":
        return self.pipeline.preprocess(release, options=ProducerOptions(onlyCache=True))

    def extract(self, release: "Release") -> "ApiDescription":
        return self.pipeline.extract(release, options=ProducerOptions(onlyCache=True))

    def diff(self, pair: "ReleasePair") -> "ApiDifference":
        return self.pipeline.diff(pair, options=ProducerOptions(onlyCache=True))

    def eval(self, pair: "ReleasePair") -> "ApiBreaking":
        return self.pipeline.eval(pair, options=ProducerOptions(onlyCache=True))

    def report(self, pair: "ReleasePair") -> "Report":
        return self.pipeline.report(pair, options=ProducerOptions(onlyCache=True))
