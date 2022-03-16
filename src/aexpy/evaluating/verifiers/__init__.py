import subprocess
import functools
from pathlib import Path
from socket import timeout
from typing import Callable
from aexpy.evaluating.checkers import EvalRule, EvalRuleCollection, ruleeval
from aexpy.evaluating.default import RuleEvaluator
from aexpy.models import ApiDifference, ApiDescription, ApiBreaking, Distribution
from aexpy.models.difference import DiffEntry
from .. import IncrementalEvaluator


def trigger(generator: "Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], list[str]]") -> "EvalRule":
    @functools.wraps(generator)
    def wrapper(entry: DiffEntry, diff: ApiDifference, old: ApiDescription, new: ApiDescription) -> None:
        tri = generator(entry, diff, old, new)
        if tri:
            entry.data["trigger"] = tri

    return ruleeval(wrapper)


class VerifyingEvaluator(IncrementalEvaluator):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "triggers"

    def basicProduce(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "ApiBreaking":
        from ..default import Evaluator
        return Evaluator(self.logger).eval(diff, old, new)

    def check(self, product: "ApiBreaking"):
        from aexpy.environments.conda import CondaEnvironment

        def checkOnDist(dist: "Distribution", name: "str" = "dist", dataId: "str" = "triggerResult"):
            try:
                with CondaEnvironment(dist.pyversion) as run:
                    res = run(
                        f"python -m pip install {dist.wheelFile}", capture_output=True, text=True)
                    self.logger.info(
                        f"Install wheel: {dist.wheelFile} with exit code {res.returncode}")
                    if res.stdout.strip():
                        self.logger.debug(f"STDOUT:\n{res.stdout}")
                    if res.stderr.strip():
                        self.logger.info(f"STDERR:\n{res.stderr}")
                    res.check_returncode()

                    for entry in product.entries.values():
                        tri = entry.data.get("trigger")
                        if isinstance(tri, list):
                            code = ";".join(str(t) for t in tri)
                            self.logger.debug(
                                f"Check {name} trigger '{code}' for {entry.id}: {entry.message}")
                            try:
                                res = run(
                                    f'python -c "{code}"', capture_output=True, text=True, timeout=60, cwd=Path(__file__).parent)
                                self.logger.info(
                                    f"Exec: '{code}' with exit code {res.returncode}")
                                if res.stdout.strip():
                                    self.logger.debug(f"STDOUT:\n{res.stdout}")
                                if res.stderr.strip():
                                    self.logger.info(f"STDERR:\n{res.stderr}")
                                entry.data[dataId] = {
                                    "exit": res.returncode,
                                    "stdout": res.stdout.splitlines(),
                                    "stderr": res.stderr.splitlines(),
                                }
                            except subprocess.TimeoutExpired as ex:
                                self.logger.error(
                                    f"Timeout checking for {entry.id}: {entry.message}", exc_info=ex)
                                if ex.stdout.strip():
                                    self.logger.debug(f"STDOUT:\n{ex.stdout}")
                                if ex.stderr.strip():
                                    self.logger.info(f"STDERR:\n{ex.stderr}")
                                entry.data[dataId] = {
                                    "exit": None,
                                    "stdout": ex.stdout.splitlines(),
                                    "stderr": ex.stderr.splitlines(),
                                }

            except Exception as ex:
                self.logger.error(
                    f"Failed to check trigger for old {dist}", exc_info=ex)

        if product.old:
            checkOnDist(product.old, "old", "triggerResultOld")
        if product.new:
            checkOnDist(product.new, "new", "triggerResultNew")

    def incrementalProcess(self, product: "ApiBreaking", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        from .generators import Triggers
        RuleEvaluator(self.logger, rules=Triggers.ruleevals).process(
            product, product, old, new)
        self.check(product)
