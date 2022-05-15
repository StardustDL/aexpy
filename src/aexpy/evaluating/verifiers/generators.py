

from typing import Callable, Hashable, Iterable, Sized
from aexpy.evaluating.checkers import EvalRule, EvalRuleCollection, ruleeval
from aexpy.evaluating.verifiers import trigger
from aexpy.models import ApiDescription, ApiDifference
from aexpy.models.description import ApiEntry, ClassEntry, ItemEntry, ItemScope, ModuleEntry, FunctionEntry, AttributeEntry, ParameterKind
from aexpy.models.difference import DiffEntry
from aexpy.utils import getObjectId


Triggers = EvalRuleCollection()


class Generator:
    def __init__(self, api: "ApiDescription") -> None:
        self.api = api

    def getParent(self, entry: "ApiEntry") -> "ApiEntry | None":
        return self.api.entries.get(entry.parent) if entry.parent else None

    def importExternalModule(self, name: "str", var: "str" = "mod"):
        return [f"import {name}", f"{var} = {name}"]

    def importModule(self, entry: "ApiEntry", var: "str" = "mod") -> "list[str]":
        if isinstance(entry, ModuleEntry):
            return [f"import {entry.id}", f"{var} = " + entry.id]
        else:
            if entry.location:
                mod = self.api.entries.get(entry.location.module)
                if isinstance(mod, ModuleEntry):
                    return self.importModule(mod)
            parent = self.getParent(entry)
            if parent and parent != entry:
                return self.importModule(parent)
        return []

    def importExternalItem(self, name: "str", var: "str" = "item"):
        moduleName, memberName = name.rsplit(".", 1)[0]
        return self.importExternalModule(moduleName) + [f"{var} = mod.{memberName}"]

    def importClass(self, entry: "ClassEntry", var: "str" = "cls"):
        return self.importModule(entry) + [f"{var} = {entry.id}"]

    def importItem(self, entry: "ItemEntry", var: "str" = "item"):
        if entry.scope == ItemScope.Instance:
            return []
        parent = self.getParent(entry)
        if parent is None:
            return []
        if isinstance(parent, ClassEntry):
            return self.importClass(parent) + [f"{var} = cls.{entry.name}"]
        else:
            return self.importModule(parent) + [f"{var} = {entry.id}"]

    def instance(self, entry: "ClassEntry", var: "str" = "inst"):
        return self.importClass(entry) + [f"{var} = object.__new__(cls)"]

    def call(self, func: "FunctionEntry", args: "list | None" = None, kwds: "dict | None" = None, var: "str" = "func"):
        args = args or []
        kwds = kwds or {}
        return self.importItem(func, var) + [f"{var}(*{repr(args)}, **{repr(kwds)})"]

    def log(self, var: "str"):
        return ["import checkers", f"checkers.log({var})"]

    def bindParameters(self, func: "str", args: "list | None" = None, kwds: "dict | None" = None, var: "str" = "args"):
        args = args or []
        kwds = kwds or {}
        return ["import checkers", f"{var} = checkers.bindParameters({func}, *{repr(args)}, **{repr(kwds)})"]

    def assertArgument(self, name: "str", value: "str", var: "str" = "args"):
        return ["import checkers", f"checkers.assertArgument({var}, {repr(name)}, {repr(value)})"]
    
    def assertArgumentDefault(self, name: "str", value: "str", var: "str" = "args"):
        return ["import checkers", f"checkers.assertArgumentDefault({var}, {repr(name)}, {repr(value)})"]

    def validParameters(self, func: "FunctionEntry", all: "bool" = False, positionFirst: "bool" = False):
        args = []
        kwds = {}

        for param in func.parameters:
            if not all and param.optional:
                continue
            if param.kind == ParameterKind.Positional:
                args.append(param.name)
            elif param.isPositional and positionFirst:
                args.append(param.name)
            elif param.isKeyword:
                kwds[param.name] = param.name

        return args, kwds


@Triggers.ruleeval
@trigger
def RemoveModule(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    return gen.importModule(entry.old) + gen.log("mod")


@Triggers.ruleeval
@trigger
def RemoveClass(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    return gen.importClass(entry.old) + gen.log("cls")


@Triggers.ruleeval
@trigger
def AddBaseClass(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


@Triggers.ruleeval
@trigger
def RemoveBaseClass(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    name: "str" = entry.data["name"]
    base = old.entries.get(name)
    ret = []

    if isinstance(base, ClassEntry):
        ret += gen.importClass(base, "base")
    else:
        ret += gen.importExternalItem(name, "base")

    if ret:
        ret += gen.importClass(entry.old) + [f"assert issubclass(cls, base)"]

    return ret


@Triggers.ruleeval
@trigger
def DeimplementAbstractBaseClass(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    name: "str" = entry.data["name"]
    ret = gen.instance(entry.old) + gen.log("inst")

    if name == getObjectId(Callable):
        ret += [f"assert callable(inst)"]
    elif name == getObjectId(Iterable):
        ret += gen.log(f"iter(inst)")
    elif name == getObjectId(Hashable):
        ret += gen.log(f"hash(inst)")
    elif name == getObjectId(Sized):
        ret += gen.log(f"len(inst)")
    else:
        return []

    return ret


@Triggers.ruleeval
@trigger
def ChangeMethodResolutionOrder(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


def removeItem(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    return gen.importItem(entry.old) + gen.log("item")


RemoveFunction = trigger(removeItem).forkind("RemoveFunction")
RemoveAttribute = trigger(removeItem).forkind("RemoveAttribute")

Triggers.ruleeval(RemoveFunction)
Triggers.ruleeval(RemoveAttribute)


@Triggers.ruleeval
@trigger
def RemoveInstanceAttribute(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


def removeAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    if isinstance(entry.old, ClassEntry):
        return gen.importClass(entry.old) + [f"alias = cls.{entry.data['name']}"] + gen.log("alias")
    else:
        return gen.importModule(entry.old) + [f"alias = mod.{entry.data['name']}"] + gen.log("alias")


def changeAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


RemoveAlias = trigger(removeAlias).forkind("RemoveAlias")
RemoveExternalAlias = trigger(removeAlias).forkind("RemoveExternalAlias")
ChangeAlias = trigger(changeAlias).forkind("ChangeAlias")
ChangeExternalAlias = trigger(changeAlias).forkind("ChangeExternalAlias")

Triggers.ruleeval(RemoveAlias)
Triggers.ruleeval(RemoveExternalAlias)
Triggers.ruleeval(ChangeAlias)
Triggers.ruleeval(ChangeExternalAlias)


def minBindParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


def maxBindParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old, True)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


AddRequiredParameter = trigger(
    minBindParameter).forkind("AddRequiredParameter")
RemoveParameterDefault = trigger(
    minBindParameter).forkind("RemoveParameterDefault")
RemoveOptionalParameter = trigger(
    maxBindParameter).forkind("RemoveOptionalParameter")
RemoveRequiredParameter = trigger(
    maxBindParameter).forkind("RemoveRequiredParameter")


Triggers.ruleeval(AddRequiredParameter)
Triggers.ruleeval(RemoveParameterDefault)
Triggers.ruleeval(RemoveOptionalParameter)
Triggers.ruleeval(RemoveRequiredParameter)


@Triggers.ruleeval
@trigger
def AddRequiredCandidate(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old)
    return gen.call(entry.old, args, kwds)


@Triggers.ruleeval
@trigger
def RemoveOptionalCandidate(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old, True)
    return gen.call(entry.old, args, kwds)


@Triggers.ruleeval
@trigger
def RemoveRequiredCandidate(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old)
    return gen.call(entry.old, args, kwds)


@Triggers.ruleeval
@trigger
def RemoveVarPositional(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    genold, gennew = Generator(old), Generator(new)
    args, kwds = genold.validParameters(entry.old)
    if isinstance(entry.old, FunctionEntry) and entry.old.varKeyword:
        nargs, nkwds = gennew.validParameters(entry.new)
        kwds.update(**nkwds)
    args.append("test_positional_arg")
    return genold.importItem(entry.old) + genold.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def RemoveVarKeyword(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    genold, gennew = Generator(old), Generator(new)
    args, kwds = genold.validParameters(entry.old)
    nargs, nkwds = gennew.validParameters(entry.new)
    kwds.update(**nkwds)
    kwds["test_keyword_arg"] = "test_keyword_arg"
    return genold.importItem(entry.old) + genold.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def AddParameterDefault(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


@Triggers.ruleeval
@trigger
def ChangeParameterDefault(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    genold, gennew = Generator(old), Generator(new)
    args, kwds = genold.validParameters(entry.old)
    if isinstance(entry.old, FunctionEntry) and entry.old.varKeyword:
        nargs, nkwds = gennew.validParameters(entry.new)
        kwds.update(**nkwds)
    oldpara = entry.data["old"]
    newpara = entry.data["new"]
    olddef = entry.data["olddefault"]
    newdef = entry.data["newdefault"]
    if oldpara == newpara:
        if olddef != None:
            return genold.importItem(entry.old) + genold.bindParameters("item", args, kwds) + genold.assertArgumentDefault(oldpara, olddef)
    return []


@Triggers.ruleeval
@trigger
def AddOptionalParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


@Triggers.ruleeval
@trigger
def MoveParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    genold, gennew = Generator(old), Generator(new)
    args, kwds = genold.validParameters(entry.old, all=True, positionFirst=True)
    if isinstance(entry.old, FunctionEntry) and entry.old.varKeyword:
        nargs, nkwds = gennew.validParameters(entry.new, all=True, positionFirst=True)
        kwds.update(**nkwds)
    name = entry.data["name"]
    oldindex = entry.data["oldindex"]
    newindex = entry.data["newindex"]
    return genold.importItem(entry.old) + genold.bindParameters("item", args, kwds) + genold.assertArgument(name, name)


@Triggers.ruleeval
@trigger
def ChangeAttributeType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


@Triggers.ruleeval
@trigger
def ChangeReturnType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []


@Triggers.ruleeval
@trigger
def ChangeParameterType(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    return []
