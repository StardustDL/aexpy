import code
import pathlib
import platform
import subprocess
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import getAppDirectory, getCacheDirectory, json
from aexpy.differing.default import Differ as BaseDiffer
from aexpy.environments.conda import CondaEnvironment
from aexpy.evaluating.default import Evaluator as BaseEvaluator
from aexpy.extracting import IncrementalExtractor
from aexpy.extracting.environments import (EnvirontmentExtractor,
                                           ExecutionEnvironment)
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.description import TRANSFER_BEGIN, FunctionEntry
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline
from aexpy.preprocessing import getDefault
from aexpy.producer import ProducerOptions
from aexpy.reporting import Reporter as Base


class PycgEnvironment(CondaEnvironment):
    __baseenvprefix__ = "pycg-extbase-"
    __envprefix__ = "pycg-ext-"
    __packages__ = ["pycg"]


def _normalizedName(name: str, topModule: str, api: "ApiDescription") -> str:
    name = name.replace("\\", "/").replace("/", ".")
    if name not in api.entries:
        tname = f"{topModule}.{name}"
        if tname in api.entries:
            return tname
    return name


class Extractor(IncrementalExtractor):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "pycg"

    def basicProduce(self, dist: "Distribution") -> "ApiDescription":
        from ..base import Extractor
        return Extractor(self.logger).extract(dist)

    def incrementalProcess(self, product: "ApiDescription", dist: "Distribution"):
        done = []

        with PycgEnvironment(dist.pyversion) as run:
            for topModule in product.distribution.topModules:
                try:
                    files = [str(item.resolve()) for item in product.distribution.wheelDir.glob(
                        f"{topModule}/**/*.py")]
                    subres = run(f"python -m pycg --package {topModule} {' '.join(files)}", text=True,
                                capture_output=True, cwd=product.distribution.wheelDir)

                    self.logger.info(
                        f"Pycg exit with {subres.returncode} for {topModule}.")

                    if subres.stdout.strip():
                        self.logger.debug(f"STDOUT:\n{subres.stdout}")
                    if subres.stderr.strip():
                        self.logger.info(f"STDERR:\n{subres.stderr}")

                    subres.check_returncode()
                    data = json.loads(subres.stdout)

                    for caller, callees in data.items():
                        caller = _normalizedName(caller, topModule, product)
                        callees = [_normalizedName(callee, topModule, product) for callee in callees]
                        entry = product.entries.get(caller)
                        if isinstance(entry, FunctionEntry):
                            entry.callees = list(set(callees))

                    done.append(topModule)
                    self.logger.info(f"Pycg done for {topModule}.")
                except Exception as ex:
                    self.logger.error(f"Pycg failed for {topModule}.", exc_info=ex)
            
            product.calcCallers()
        
        assert len(done) > 0, "No modules processed by pycg."
