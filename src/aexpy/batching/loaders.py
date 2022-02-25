
from aexpy.env import getPipeline
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, ReleasePair, Report)
from aexpy.pipelines import Pipeline
from aexpy.producer import ProducerOptions

from .generators import (diffed, evaluated, extracted, pair, preprocessed,
                         reported, single)


class BatchLoader:
    def __init__(self, project: "str", pipeline: "Pipeline | None" = None) -> None:
        self.project = project
        self.pipeline = pipeline or getPipeline()

    def index(self):
        self.releases = single(self.project)
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
