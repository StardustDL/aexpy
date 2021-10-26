from uuid import uuid1

from aexpy import fsutils
from aexpy.analyses.models import (ApiCollection, ApiEntry, ApiManifest,
                                   ClassEntry, AttributeEntry, FunctionEntry,
                                   ModuleEntry, Parameter, ParameterKind)
from aexpy.env import env

from . import serializer
from .models import DiffCollection, DiffEntry, DiffRule


class Differ:
    def __init__(self) -> None:
        self.rules: list[DiffRule] = []

    def with_default_rules(self):
        from .rules import (addrules, memberrules, otherrules, pararules,
                            removerules)
        self.rules.extend(addrules)
        self.rules.extend(removerules)
        self.rules.extend(memberrules)
        self.rules.extend(pararules)
        self.rules.extend(otherrules)
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
