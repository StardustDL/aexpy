import subprocess
import functools
from pathlib import Path
from socket import timeout
from typing import Callable
from aexpy.evaluating.checkers import EvalRule, EvalRuleCollection, ruleeval
from aexpy.evaluating.default import RuleEvaluator
from aexpy.models import ApiDifference, ApiDescription, ApiBreaking, Distribution
from aexpy.models.difference import BreakingRank, DiffEntry, VerifyState
from .. import IncrementalEvaluator


def trigger(generator: "Callable[[DiffEntry, ApiDifference, ApiDescription, ApiDescription], list[str]]") -> "EvalRule":
    @functools.wraps(generator)
    def wrapper(entry: DiffEntry, diff: ApiDifference, old: ApiDescription, new: ApiDescription) -> None:
        if entry.rank == BreakingRank.Compatible or entry.rank == BreakingRank.Unknown:
            return
        tri = generator(entry, diff, old, new)
        if tri:
            entry.data["verify"] = {"trigger": tri}

    return ruleeval(wrapper)


class Verifier(IncrementalEvaluator):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "verify"

    def basicProduce(self, diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "ApiBreaking":
        from ..default import Evaluator
        return Evaluator(self.logger).eval(diff, old, new)

    def check(self, product: "ApiBreaking"):
        from aexpy.environments.conda import CondaEnvironment

        def checkOnDist(dist: "Distribution", name: "str" = "dist", dataId: "str" = "result"):
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
                        verify: "dict" = entry.data.get("verify")
                        if verify is None:
                            continue
                        tri = verify.get("trigger")
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
                                verify[dataId] = {
                                    "exit": res.returncode,
                                    "out": res.stdout.splitlines(),
                                    "err": res.stderr.splitlines(),
                                }
                            except subprocess.TimeoutExpired as ex:
                                self.logger.error(
                                    f"Timeout checking for {entry.id}: {entry.message}", exc_info=ex)
                                if ex.stdout.strip():
                                    self.logger.debug(f"STDOUT:\n{ex.stdout}")
                                if ex.stderr.strip():
                                    self.logger.info(f"STDERR:\n{ex.stderr}")
                                verify[dataId] = {
                                    "exit": None,
                                    "out": ex.stdout.splitlines(),
                                    "err": ex.stderr.splitlines(),
                                }

            except Exception as ex:
                self.logger.error(
                    f"Failed to check trigger for old {dist}", exc_info=ex)

        if product.old:
            checkOnDist(product.old, "old", "old")
        if product.new:
            checkOnDist(product.new, "new", "new")

        for entry in product.entries.values():
            verify = entry.data.get("verify")
            if verify is None:
                continue
            old = verify.get("old")
            new = verify.get("new")
            if old is None or new is None:
                continue
            oexit = old.get("exit")
            nexit = new.get("exit")
            if oexit is None or nexit is None:
                continue
            if oexit != 0:
                continue
            entry.verify.state = VerifyState.Pass if nexit != 0 else VerifyState.Fail
            entry.verify.verifier = self.id()

    def incrementalProcess(self, product: "ApiBreaking", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        from .generators import Triggers
        RuleEvaluator(self.logger, rules=Triggers.ruleevals).process(
            product, product, old, new)
        self.check(product)
