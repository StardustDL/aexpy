from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy.models import DiffEntry
from aexpy.producer import ProducerOptions

from ..models import ApiBreaking, ApiDifference
from . import DefaultEvaluator
from .checkers import RuleEvaluator


class RuleEvaluator(DefaultEvaluator):
    """Evaluator based on rules."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[RuleEvaluator] | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.rules: "list[RuleEvaluator]" = rules or []

    def process(self, product: "ApiBreaking", diff: "ApiDifference"):
        for entry in diff.entries.values():
            for rule in self.rules:
                rule(entry, diff)
            product.entries.update({entry.id: entry})


class Evaluator(RuleEvaluator):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[RuleEvaluator] | None" = None) -> None:
        rules = rules or []
        from .evals import RuleEvals
        rules.extend(RuleEvals.ruleevals)

        super().__init__(logger, cache, options, rules)
