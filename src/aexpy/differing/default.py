from logging import Logger
from pathlib import Path
from uuid import uuid1
from aexpy.extracting.main.base import islocal

from aexpy.models.description import ApiEntry, ClassEntry, CollectionEntry, ModuleEntry
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
            if islocal(v.id):
                # ignore unaccessable local elements
                continue
            newentry = new.entries.get(k)
            if newentry is not None and islocal(newentry.id):
                continue
            product.entries.update(
                {e.id: e for e in self._processEntry(v, newentry, old, new)})

        for k, v in new.entries.items():
            if islocal(v.id):
                # ignore unaccessable local elements
                continue
            if k not in old.entries:
                product.entries.update(
                    {e.id: e for e in self._processEntry(None, v, old, new)})

    def _processEntry(self, old: "ApiEntry | None", new: "ApiEntry | None", oldDescription: "ApiDescription", newDescription: "ApiDescription") -> "list[DiffEntry]":
        self.logger.debug(f"Differ {old} and {new}.")
        result = []
        for rule in self.rules:
            try:
                done: "list[DiffEntry]" = rule(
                    old, new, oldDescription, newDescription)
                if done:
                    for item in done:
                        if not item.id:
                            item.id = str(uuid1())
                        result.append(item)
            except Exception as ex:
                self.logger.error(
                    f"Failed to differ {old} and {new} by rule {rule.kind} ({rule.checker}).", exc_info=ex)
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

    def _processEntry(self, old: "ApiEntry | None", new: "ApiEntry | None", oldDescription: "ApiDescription", newDescription: "ApiDescription") -> "list[DiffEntry]":
        # ignore sub-class overidden method removing, alias by name resolving
        if old is None and new is not None:
            told = oldDescription.resolveName(new.id)
            if told.__class__ == new.__class__:
                old = told
        if new is None and old is not None:
            tnew = newDescription.resolveName(old.id)
            if tnew.__class__ == old.__class__:
                new = tnew
        return super()._processEntry(old, new, oldDescription, newDescription)