from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy.models.description import ApiEntry
from aexpy.models.difference import DiffEntry
from aexpy.producer import ProducerOptions

from .checkers import DiffRule
from ..models import ApiDifference, Distribution, ApiDescription
from . import Differ as Base


class Differ(Base):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.rules: "list[DiffRule]" = []

        from .rules import (modules, classes, functions,
                            attributes, parameters, types, aliases, externals)
        self.rules.extend(modules.ModuleRules.rules)
        self.rules.extend(classes.ClassRules.rules)
        self.rules.extend(functions.FunctionRules.rules)
        self.rules.extend(attributes.AttributeRules.rules)
        self.rules.extend(parameters.ParameterRules.rules)
        # self.rules.extend(types.TypeRules.rules)
        self.rules.extend(aliases.AliasRules.rules)
        self.rules.extend(externals.ExternalRules.rules)

    def diff(self, old: "ApiDescription", new: "ApiDescription") -> "ApiDifference":
        cacheFile = self.cache / old.distribution.release.project / \
            f"{old.distribution.release}&{new.distribution.release}.json" if self.cached else None

        with ApiDifference(old=old.distribution, new=new.distribution).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None:
                for k, v in old.entries.items():
                    ret.entries.update(
                        {e.id: e for e in self._processEntry(v, new.entries.get(k), old, new)})

                for k, v in new.entries.items():
                    if k not in old.entries:
                        ret.entries.update(
                            {e.id: e for e in self._processEntry(None, v, old, new)})

        return ret

    def _processEntry(self, old: "ApiEntry", new: "ApiEntry", oldDescription: "ApiDescription", newDescription: "ApiDescription") -> "list[DiffEntry]":
        result = []
        for rule in self.rules:
            done: DiffEntry | None = rule(
                old, new, oldDescription, newDescription)
            if done:
                if not done.id:
                    done.id = str(uuid1())
                result.append(done)
        return result
