from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy.models import DiffEntry
from aexpy.producer import ProducerOptions

from ..models import ApiBreaking, ApiDescription, ApiDifference
from . import DefaultEvaluator
from .checkers import EvalRule


class RuleEvaluator(DefaultEvaluator):
    """Evaluator based on rules."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[EvalRule] | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.rules: "list[EvalRule]" = rules or []

    def process(self, product: "ApiBreaking", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription"):
        for entry in diff.entries.values():
            self.logger.debug(f"Evaluate entry {entry.id}: {entry.message}.")

            for rule in self.rules:
                try:
                    rule(entry, diff, old, new)
                except Exception as ex:
                    self.logger.error(
                        f"Failed to evaluate entry {entry.id} ({entry.message}) by rule {rule.kind} ({rule.checker}).", exc_info=ex)
            product.entries.update({entry.id: entry})


class Evaluator(RuleEvaluator):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "base"

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[EvalRule] | None" = None) -> None:
        rules = rules or []
        from .evals import RuleEvals
        rules.extend(RuleEvals.ruleevals)

        super().__init__(logger, cache, options, rules)
