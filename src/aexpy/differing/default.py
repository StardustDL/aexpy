from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy.models.description import ApiEntry
from aexpy.models.difference import DiffEntry
from aexpy.producer import ProducerOptions

from ..models import ApiDescription, ApiDifference, Distribution
from . import DefaultDiffer
from .checkers import DiffRule


class RuleDiffer(DefaultDiffer):
    """Differ based on diff rules."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[DiffRule] | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.rules: "list[DiffRule]" = rules or []

    def process(self, product: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> None:
        for k, v in old.entries.items():
            product.entries.update(
                {e.id: e for e in self._processEntry(v, new.entries.get(k), old, new)})

        for k, v in new.entries.items():
            if k not in old.entries:
                product.entries.update(
                    {e.id: e for e in self._processEntry(None, v, old, new)})

    def _processEntry(self, old: "ApiEntry", new: "ApiEntry", oldDescription: "ApiDescription", newDescription: "ApiDescription") -> "list[DiffEntry]":
        result = []
        for rule in self.rules:
            done: "list[DiffEntry]" = rule(
                old, new, oldDescription, newDescription)
            if done:
                for item in done:
                    if not item.id:
                        item.id = str(uuid1())
                    result.append(item)
        return result


class Differ(RuleDiffer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, rules: "list[DiffRule] | None" = None) -> None:
        rules = rules or []

        from .rules import (aliases, attributes, classes, externals, functions,
                            modules, parameters, types)
        rules.extend(modules.ModuleRules.rules)
        rules.extend(classes.ClassRules.rules)
        rules.extend(functions.FunctionRules.rules)
        rules.extend(attributes.AttributeRules.rules)
        rules.extend(parameters.ParameterRules.rules)
        rules.extend(types.TypeRules.rules)
        rules.extend(aliases.AliasRules.rules)
        rules.extend(externals.ExternalRules.rules)

        super().__init__(logger, cache, options, rules)
