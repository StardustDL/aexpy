
from aexpy.env import getPipeline
from aexpy.models import Release, ReleasePair, Distribution, ApiDescription, ApiDifference, ApiBreaking, Report
from aexpy.pipelines import Pipeline
from .generators import single, pair, preprocessed, extracted, diffed, evaluated, reported


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
        return self.pipeline.preprocess(release, onlyCache=True)

    def extract(self, release: "Release") -> "ApiDescription":
        return self.pipeline.extract(release, onlyCache=True)

    def diff(self, pair: "ReleasePair") -> "ApiDifference":
        return self.pipeline.diff(pair, onlyCache=True)

    def eval(self, pair: "ReleasePair") -> "ApiBreaking":
        return self.pipeline.eval(pair, onlyCache=True)

    def report(self, pair: "ReleasePair") -> "Report":
        return self.pipeline.report(pair, onlyCache=True)
