from typing import List, Optional

from uuid import uuid1
from aexpy.analyses.models import ApiCollection, ApiEntry, ApiManifest, ClassEntry, FieldEntry, FunctionEntry, ModuleEntry, Parameter, ParameterKind
from aexpy.env import env
from aexpy import fsutils
from .models import DiffCollection, DiffEntry, DiffRule
from . import serializer


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



def diff(old: ApiCollection, new: ApiCollection, redo: bool = False):
    name = f"{old.manifest.project}@{old.manifest.version}-{new.manifest.project}@{new.manifest.version}"
    cache = env.cache.joinpath("diff")
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{name}.json")
    if not cacheFile.exists() or redo:
        result = Differ().with_default_rules().process(old, new)
        cacheFile.write_text(serializer.serialize(result))
        return result

    return serializer.deserialize(cacheFile.read_text())


if __name__ == "__main__":
    old = ApiCollection(ApiManifest("test", "1"))
    old.addEntry(ModuleEntry(id="mod"))
    old.addEntry(ModuleEntry(id="mod0", members={"m1": "", "m2": ""}))
    old.addEntry(ClassEntry(id="cls"))
    old.addEntry(ClassEntry(id="cls0", bases=["b1"]))
    old.addEntry(FunctionEntry(id="func"))
    old.addEntry(FunctionEntry(id="func0", returnType="str", parameters=[
        Parameter(ParameterKind.PositionalOrKeyword, name="a"),
        Parameter(ParameterKind.PositionalOrKeyword, name="c", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="e"),
        Parameter(ParameterKind.PositionalOrKeyword, name="f", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="g", optional=True, default="1"),
        Parameter(ParameterKind.PositionalOrKeyword, name="h", type="int"),
        Parameter(ParameterKind.VarPositional, name="i"),
        Parameter(ParameterKind.VarKeyword, name="j"),
    ]))
    old.addEntry(FieldEntry(id="field"))
    old.addEntry(FieldEntry(id="field0", type="str"))

    new = ApiCollection(ApiManifest("test", "2"))
    new.addEntry(ModuleEntry(id="mod2"))
    new.addEntry(ModuleEntry(id="mod0", members={"m2": "changed", "m3": ""}))
    new.addEntry(ClassEntry(id="cls2"))
    new.addEntry(ClassEntry(id="cls0", bases=["b2"]))
    new.addEntry(FunctionEntry(id="func2"))
    new.addEntry(FunctionEntry(id="func0", returnType="int", parameters=[
        Parameter(ParameterKind.PositionalOrKeyword, name="b"),
        Parameter(ParameterKind.PositionalOrKeyword, name="d", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="e", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="f"),
        Parameter(ParameterKind.PositionalOrKeyword, name="g", optional=True, default="2"),
        Parameter(ParameterKind.PositionalOrKeyword, name="h", type="str"),
    ]))
    new.addEntry(FieldEntry(id="field2"))
    new.addEntry(FieldEntry(id="field0", type="int"))

    result = Differ().with_default_rules().process(old, new)

    for item in result.entries.values():
        print(item.kind, item.message)
