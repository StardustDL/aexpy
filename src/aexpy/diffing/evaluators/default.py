from logging import Logger
from typing import override

from .. import Differ
from .checkers import EvalRule


class RuleEvaluator(Differ):
    """Evaluator based on rules."""

    def __init__(
        self, /, logger: Logger | None = None, rules: list[EvalRule] | None = None
    ) -> None:
        super().__init__(logger)
        self.rules = rules or []

    @override
    def diff(self, /, old, new, product):
        for entry in product.entries.values():
            self.logger.debug(f"Evaluate entry {entry.id}: {entry.message}.")

            for rule in self.rules:
                try:
                    rule(entry, product, old, new)
                except Exception:
                    self.logger.error(
                        f"Failed to evaluate entry {entry.id} ({entry.message}) by rule {rule.kind} ({rule.checker}).",
                        exc_info=True,
                    )
            product.entries.update({entry.id: entry})


class DefaultEvaluator(RuleEvaluator):
    def __init__(
        self, /, logger: Logger | None = None, rules: list[EvalRule] | None = None
    ) -> None:
        rules = rules or []

        from .evals import RuleEvals

        rules.extend(RuleEvals.rules)

        super().__init__(logger, rules)
