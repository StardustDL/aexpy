from hashlib import blake2b
from logging import Logger
from typing import Iterable, override
from uuid import uuid1

from ...models import ApiDescription
from ...models.description import ApiEntry
from ...models.difference import DiffEntry
from ...utils import isLocal
from .. import Differ
from .checkers import DiffConstraint


def hashDiffEntry(entry: DiffEntry):
    return blake2b(
        f"{entry.rank} {entry.kind} {entry.message}".encode(), digest_size=4
    ).hexdigest()


class ConstraintDiffer(Differ):
    """Diff based on diff constraints."""

    def __init__(
        self,
        /,
        logger: Logger | None = None,
        constraints: list[DiffConstraint] | None = None,
    ) -> None:
        super().__init__(logger)
        self.constraints: list[DiffConstraint] = constraints or []

    @override
    def diff(self, /, old, new, product):
        for v in old:
            if isLocal(v.id):
                # ignore unaccessable local elements
                continue
            newentry = new[v.id]
            if newentry is not None and isLocal(newentry.id):
                continue
            for e in self.process(v, newentry, old, new):
                if e.id in product.entries:
                    self.logger.warning(f"Existed entry id  {e.id}: {e}")
                    e.id += f"-{uuid1()}"
                    assert (
                        e.id not in product.entries
                    ), f"Still existed entry id {e.id}: {e}"
                product.entries[e.id] = e

        for v in new:
            if isLocal(v.id):
                # ignore unaccessable local elements
                continue
            if v.id not in old:
                product.entries.update(
                    {e.id: e for e in self.process(None, v, old, new)}
                )

    def process(
        self,
        /,
        old: ApiEntry | None,
        new: ApiEntry | None,
        oldDescription: ApiDescription,
        newDescription: ApiDescription,
    ) -> Iterable[DiffEntry]:
        self.logger.debug(f"Diff {old} and {new}.")
        for constraint in self.constraints:
            try:
                for item in constraint(old, new, oldDescription, newDescription):
                    if not item.id:
                        item.id = hashDiffEntry(item)
                    yield item
            except Exception:
                self.logger.error(
                    f"Failed to diff {old} and {new} by constraints {constraint.kind} ({constraint.checker}).",
                    exc_info=True,
                )


class DefaultDiffer(ConstraintDiffer):
    def __init__(
        self,
        /,
        logger: Logger | None = None,
        constraints: list[DiffConstraint] | None = None,
    ) -> None:
        constraints = constraints or []

        from .contraints import (aliases, attributes, classes, externals,
                                 functions, modules, parameters, types)

        constraints.extend(modules.ModuleConstraints.constraints)
        constraints.extend(classes.ClassConstraints.constraints)
        constraints.extend(functions.FunctionConstraints.constraints)
        constraints.extend(attributes.AttributeConstraints.constraints)
        constraints.extend(parameters.ParameterConstraints.constraints)
        constraints.extend(types.TypeConstraints.constraints)
        constraints.extend(aliases.AliasConstraints.constraints)
        constraints.extend(externals.ExternalConstraints.constraints)

        super().__init__(logger, constraints)

    @override
    def process(self, /, old, new, oldDescription, newDescription):
        # ignore sub-class overidden method removing, alias by name resolving
        if old is None and new is not None:
            told = oldDescription.resolve(new.id)
            if told.__class__ == new.__class__:
                old = told
        if new is None and old is not None:
            tnew = newDescription.resolve(old.id)
            if tnew.__class__ == old.__class__:
                new = tnew
        return super().process(old, new, oldDescription, newDescription)
