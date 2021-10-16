from typing import Optional
from aexpy.analyses.models import ApiEntry, CollectionEntry, ModuleEntry, ClassEntry, FunctionEntry, FieldEntry
from .models import DiffRule, RuleCheckResult


def add(a: Optional[ApiEntry], b: Optional[ApiEntry]):
    if a is None and b is not None:
        return RuleCheckResult(True, f"Add {b.name}")
    return RuleCheckResult.unsatisfied()


def remove(a: Optional[ApiEntry], b: Optional[ApiEntry]):
    if a is not None and b is None:
        return RuleCheckResult(True, f"Remove {a.name}")
    return RuleCheckResult.unsatisfied()


def addMember(a: Optional[CollectionEntry], b: Optional[CollectionEntry]):
    sub = b.members.keys() - a.members.keys()
    if len(sub) > 0:
        return RuleCheckResult(True, f"Add member: {list(sub)}")
    return RuleCheckResult.unsatisfied()


def removeMember(a: Optional[CollectionEntry], b: Optional[CollectionEntry]):
    sub = a.members.keys() - b.members.keys()
    if len(sub) > 0:
        return RuleCheckResult(True, f"Remove member: {list(sub)}")
    return RuleCheckResult.unsatisfied()


def changeMember(a: Optional[CollectionEntry], b: Optional[CollectionEntry]):
    inter = a.members.keys() & b.members.keys()
    changed = {}
    for k in inter:
        if a.members[k] != b.members[k]:
            changed[k] = f"{a.members[k]} -> {b.members[k]}"
    if len(changed) > 0:
        return RuleCheckResult(True, f"Remove member: {changed}")
    return RuleCheckResult.unsatisfied()


def changeBases(a: Optional[ClassEntry], b: Optional[ClassEntry]):
    changed = a ^ b
    if len(changed) > 0:
        return RuleCheckResult(True, f"Base class changed: {changed}")
    return RuleCheckResult.unsatisfied()


def changeFieldType(a: Optional[FieldEntry], b: Optional[FieldEntry]):
    if a.type != b.type:
        return RuleCheckResult(True, f"Field type changed: {a.type} -> {b.type}")
    return RuleCheckResult.unsatisfied()


def changeReturnType(a: Optional[FunctionEntry], b: Optional[FunctionEntry]):
    if a.returnType != b.returnType:
        return RuleCheckResult(True, f"Return type changed: {a.returnType} -> {b.returnType}")
    return RuleCheckResult.unsatisfied()


addrules = [
    DiffRule("AddModule", add).fortype(ModuleEntry, True),
    DiffRule("AddClass", add).fortype(ClassEntry, True),
    DiffRule("AddFunction", add).fortype(FunctionEntry, True),
    DiffRule("AddField", add).fortype(FieldEntry, True),
]

removerules = [
    DiffRule("RemoveModule", remove).fortype(ModuleEntry, True),
    DiffRule("RemoveClass", remove).fortype(ClassEntry, True),
    DiffRule("RemoveFunction", remove).fortype(FunctionEntry, True),
    DiffRule("RemoveField", remove).fortype(FieldEntry, True),
]

memberrules = [
    DiffRule("AddMember", addMember).fortype(CollectionEntry),
    DiffRule("RemoveMember", removeMember).fortype(CollectionEntry),
    DiffRule("ChangeMember", changeMember).fortype(CollectionEntry)
]

pararules = []

otherrules = [
    DiffRule("ChangeBaseClass", changeBases).fortype(ClassEntry),
    DiffRule("ChangeFieldType", changeFieldType).fortype(FieldEntry),
    DiffRule("ChangeReturnType", changeReturnType).fortype(FunctionEntry),
]
