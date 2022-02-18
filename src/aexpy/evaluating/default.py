from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy.models import DiffEntry
from aexpy.producer import ProducerOptions

from .checkers import RuleEvaluator
from ..models import ApiDifference, ApiBreaking
from . import DefaultEvaluator


class RuleEvaluator(DefaultEvaluator):
    """Evaluator based on rules."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[RuleEvaluator] | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.rules: "list[RuleEvaluator]" = rules or []

    def process(self, product: "ApiBreaking", diff: "ApiDifference"):
        for entry in diff.entries.values():
            for rule in self.rules:
                done: "list[DiffEntry]" = rule(entry, diff)
                if done:
                    for item in done:
                        if not item.id:
                            item.id = str(uuid1())
                    product.entries.update({i.id: i for i in done})


class Evaluator(RuleEvaluator):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[RuleEvaluator] | None" = None) -> None:
        rules = rules or []
        from .evals import RuleEvals
        rules.extend(RuleEvals.ruleevals)

        super().__init__(logger, cache, options, rules)
