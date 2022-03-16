

from aexpy.evaluating.checkers import EvalRuleCollection
from aexpy.evaluating.triggers import trigger
from aexpy.extracting.main.basic import importModule
from aexpy.models import ApiDescription, ApiDifference
from aexpy.models.description import ApiEntry, ClassEntry, ItemEntry, ModuleEntry, FunctionEntry, AttributeEntry, ParameterKind
from aexpy.models.difference import DiffEntry


Triggers = EvalRuleCollection()


class Generator:
    def __init__(self, api: "ApiDescription") -> None:
        self.api = api

    def getParent(self, entry: "ApiEntry") -> "ApiEntry | None":
        id = entry.id.removesuffix(f'.{entry.name}')
        return self.api.entries.get(id)

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

    def importClass(self, entry: "ClassEntry", var: "str" = "cls"):
        return self.importModule(entry) + [f"{var} = {entry.id}"]

    def importItem(self, entry: "ItemEntry", var: "str" = "item"):
        if entry.bound:
            return []
        parent = self.getParent(entry)
        if parent is None:
            return []
        if isinstance(parent, ClassEntry):
            return self.importClass(parent) + [f"{var} = cls.{entry.name}"]
        else:
            return self.importModule(parent) + [f"{var} = {entry.id}"]

    def log(self, var: "str"):
        return ["import checkers", f"checkers.log({var})"]

    def bindParameters(self, func: "str", args: "list | None" = None, kwds: "dict | None" = None):
        args = args or []
        kwds = kwds or {}
        return ["import checkers", f"checkers.bindParameters({func}, *{repr(args)}, **{repr(kwds)})"]

    def call(self, func: "FunctionEntry", args: "list | None" = None, kwds: "dict | None" = None, var: "str" = "func"):
        args = args or []
        kwds = kwds or {}
        return self.importItem(func, var) + [f"{var}(*{repr(args)}, **{repr(kwds)})"]

    def validParameters(self, func: "FunctionEntry", all: "bool" = False):
        args = []
        kwds = {}

        for param in func.parameters:
            if not all and param.optional:
                continue
            if param.kind == ParameterKind.Positional:
                args.append(param.name)
            elif param.isKeyword:
                kwds[param.name] = param.default
            elif param.kind == ParameterKind.VarPositional and all:
                args.append("test_var_positional")
            elif param.kind == ParameterKind.VarKeyword and all:
                kwds["test_var_keyword"] = "test_var_keyword"

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
def RemoveFunction(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    return gen.importItem(entry.old) + gen.log("item")


@Triggers.ruleeval
@trigger
def RemoveAttribute(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    return gen.importItem(entry.old) + gen.log("item")


@Triggers.ruleeval
@trigger
def RemoveAlias(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    if isinstance(entry.old, ClassEntry):
        return gen.importClass(entry.old) + [f"alias = cls.{entry.data['name']}"] + gen.log("alias")
    else:
        return gen.importModule(entry.old) + [f"alias = mod.{entry.data['name']}"] + gen.log("alias")


@Triggers.ruleeval
@trigger
def AddRequiredParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def RemoveParameterDefault(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def RemoveVarPositional(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old, True)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def RemoveVarKeyword(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old, True)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def RemoveOptionalParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old, True)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)


@Triggers.ruleeval
@trigger
def RemoveRequiredParameter(entry: "DiffEntry", diff: "ApiDifference", old: "ApiDescription", new: "ApiDescription") -> "list[str]":
    gen = Generator(old)
    args, kwds = gen.validParameters(entry.old, True)
    return gen.importItem(entry.old) + gen.bindParameters("item", args, kwds)
