from logging import Logger
from pathlib import Path
from uuid import uuid1
from aexpy.extracting.main.base import islocal

from aexpy.models.description import ApiEntry, ClassEntry, CollectionEntry, ModuleEntry
from aexpy.models.difference import DiffEntry
from aexpy.producers import ProducerOptions

from aexpy.models import ApiDescription, ApiDifference, Distribution
from .. import Differ
from .checkers import DiffConstraint


class ConstraintDiffer(Differ):
    """Diff based on diff constraints."""

    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, constraints: "list[DiffConstraint] | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.constraints: "list[DiffConstraint]" = constraints or []

    def diff(self, old: "ApiDescription", new: "ApiDescription", product: "ApiDifference"):
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
        self.logger.debug(f"Diff {old} and {new}.")
        result = []
        for constraint in self.constraints:
            try:
                done: "list[DiffEntry]" = constraint(
                    old, new, oldDescription, newDescription)
                if done:
                    for item in done:
                        if not item.id:
                            item.id = str(uuid1())
                        result.append(item)
            except Exception as ex:
                self.logger.error(
                    f"Failed to diff {old} and {new} by constraints {constraint.kind} ({constraint.checker}).", exc_info=ex)
        return result


class DefaultDiffer(ConstraintDiffer):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None, constraints: "list[DiffConstraint] | None" = None) -> None:
        constraints = constraints or []

        from .contraints import (aliases, attributes, classes, externals, functions,
                                 modules, parameters, types)
        constraints.extend(modules.ModuleRules.constraints)
        constraints.extend(classes.ClassRules.constraints)
        constraints.extend(functions.FunctionRules.constraints)
        constraints.extend(attributes.AttributeRules.constraints)
        constraints.extend(parameters.ParameterRules.constraints)
        constraints.extend(types.TypeRules.constraints)
        constraints.extend(aliases.AliasRules.constraints)
        constraints.extend(externals.ExternalRules.constraints)

        super().__init__(logger, cache, options, constraints)

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
