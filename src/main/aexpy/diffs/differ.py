from typing import List, Optional

from uuid import uuid1
from aexpy.analyses.models import ApiCollection, ApiEntry
from .models import DiffCollection, DiffEntry, DiffRule


class Differ:
    def __init__(self) -> None:
        self.rules: List[DiffRule] = []

    def with_default_rules(self):
        from .rules import addrules, removerules, memberrules, otherrules, pararules
        self.rules.extend(addrules)
        self.rules.extend(removerules)
        self.rules.extend(memberrules)
        self.rules.extend(pararules)
        self.rules.extend(otherrules)
        return self

    def _processEntry(self, old: ApiEntry, new: ApiEntry) -> List[DiffEntry]:
        result = []
        for rule in self.rules:
            done: Optional[DiffEntry] = rule(old, new)
            if done:
                if not done.id:
                    done.id = uuid1()
                result.append(done)
        return result

    def process(self, old: ApiCollection, new: ApiCollection) -> DiffCollection:
        result = DiffCollection(old=old.manifest, new=new.manifest)

        for k, v in old.entries.items():
            if k in new.entries:
                newV = new.entries[k]
            else:
                newV = None
            result.entries.update(
                {e.id: e for e in self._processEntry(v, newV)})

        for k, v in new.entries.items():
            if k in old.entries:
                continue
            result.entries.update(
                {e.id: e for e in self._processEntry(None, v)})

        return result
