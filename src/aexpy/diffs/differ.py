from uuid import uuid1

from aexpy import utils
from aexpy.analyses.models import (ApiCollection, ApiEntry, ApiManifest,
                                   AttributeEntry, ClassEntry, FunctionEntry,
                                   ModuleEntry, Parameter, ParameterKind)
from aexpy.env import env

from . import serializer
from .models import DiffCollection, DiffEntry, DiffRule


class Differ:
    def __init__(self) -> None:
        self.rules: list[DiffRule] = []

    def with_default_rules(self):
        from .rules import (AddRules, MemberRules, OtherRules, ParameterRules,
                            RemoveRules)
        self.rules.extend(AddRules.rules)
        self.rules.extend(RemoveRules.rules)
        self.rules.extend(MemberRules.rules)
        self.rules.extend(ParameterRules.rules)
        self.rules.extend(OtherRules.rules)
        return self

    def _processEntry(self, old: ApiEntry, new: ApiEntry) -> list[DiffEntry]:
        result = []
        for rule in self.rules:
            done: DiffEntry | None = rule(old, new)
            if done:
                if not done.id:
                    done.id = str(uuid1())
                result.append(done)
        return result

    def process(self, old: ApiCollection, new: ApiCollection) -> DiffCollection:
        result = DiffCollection(old=old.manifest, new=new.manifest)

        for k, v in old.entries.items():
            result.entries.update(
                {e.id: e for e in self._processEntry(v, new.entries.get(k))})

        for k, v in new.entries.items():
            if k in old.entries:
                continue
            result.entries.update(
                {e.id: e for e in self._processEntry(None, v)})

        return result
