
from logging import Logger
from pathlib import Path
from typing import Iterable

from aexpy.batching import Batcher, InProcessBatcher
from aexpy.env import env
from aexpy.models import (ApiDescription, ApiDifference,
                          Distribution, BatchResult, ProduceMode, Release, ReleasePair,
                          Report)
from aexpy.pipelines import Pipeline
from aexpy.producers import ProducerOptions

from .generators import (diffed, extracted, pair, preprocessed,
                         reported, single)


class BatchIndexer:
    def __init__(self, provider: "str | None" = None) -> None:
        self.pipeline = env.build(provider or "")

    def index(self, project: str):
        self.releases = single(project)
        self.preprocessed = list(
            filter(preprocessed(self.pipeline), self.releases))
        self.extracted = list(
            filter(extracted(self.pipeline), self.preprocessed))
        self.pairs = pair(self.extracted)
        self.diffed = list(filter(diffed(self.pipeline), self.pairs))
        self.reported = list(filter(reported(self.pipeline), self.diffed))

    def preprocess(self, release: "Release") -> "Distribution":
        return self.pipeline.preprocess(release, ProduceMode.Read)

    def extract(self, release: "Release") -> "ApiDescription":
        return self.pipeline.extract(release, ProduceMode.Read)

    def diff(self, pair: "ReleasePair") -> "ApiDifference":
        return self.pipeline.diff(pair, ProduceMode.Read)

    def report(self, pair: "ReleasePair") -> "Report":
        return self.pipeline.report(pair, ProduceMode.Read)

    def preprocessAll(self) -> "Iterable[Distribution]":
        for item in self.preprocessed:
            yield self.preprocess(item)

    def extractAll(self) -> "Iterable[ApiDescription]":
        for item in self.extracted:
            yield self.extract(item)

    def diffAll(self) -> "Iterable[ApiDifference]":
        for item in self.diffed:
            yield self.diff(item)

    def reportAll(self) -> "Iterable[Report]":
        for item in self.reported:
            yield self.report(item)
