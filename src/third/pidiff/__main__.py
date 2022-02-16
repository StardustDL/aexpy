import code
from logging import Logger
import pathlib
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.reporting import Reporter as Base
from . import Evaluator, EmptyPipeline, getDefault, Release


class Reporter(Base):
    def stage(self):
        return "pidiff-report"

    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        from aexpy.reporting.default import Reporter
        return Reporter(self.logger, self.cache, self.redo).report(oldRelease, newRelease, oldDistribution, newDistribution, oldDescription, newDescription, diff, bc)


if __name__ == "__main__":
    pipeline = EmptyPipeline(evaluator=Evaluator(
    ), preprocessor=getDefault(), reporter=Reporter())

    # pipeline.report(Release("coxbuild", "0.1.5"), Release("coxbuild", "0.1.6"))
    pipeline.report(Release("more-executors", "1.15.0"),Release("more-executors", "1.16.0"))
    # res = pipeline.eval(Release("more-executors", "1.15.0"),Release("more-executors", "1.16.0"))

    # code.interact(banner="", local=locals())
