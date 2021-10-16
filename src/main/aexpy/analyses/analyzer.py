from typing import Dict, List, Set, cast
from .models import ApiCollection, ApiEntry, FunctionEntry, FieldEntry, ModuleEntry, ClassEntry, Parameter, ParameterKind, SpecialEntry, SpecialKind
from uuid import uuid1
from types import ModuleType
import inspect
import os
import logging
import ast
import shutil


def _qualname(obj, default_name=None):
    if hasattr(obj, "__qualname__") and hasattr(obj, "__module__"):
        return f"{obj.__module__}.{obj.__qualname__}"
    if default_name is None:
        raise Exception("None for default_name.")
    return default_name


PARA_KIND_MAP = {
    inspect.Parameter.KEYWORD_ONLY: ParameterKind.Keyword,
    inspect.Parameter.VAR_KEYWORD: ParameterKind.VarKeyword,
    inspect.Parameter.VAR_POSITIONAL: ParameterKind.VarPositional,
    inspect.Parameter.POSITIONAL_ONLY: ParameterKind.Positional,
    inspect.Parameter.POSITIONAL_OR_KEYWORD: ParameterKind.PositionalOrKeyword,
}

class Analyzer:
    _logger = logging.getLogger("analyzer")

    def __init__(self) -> None:
        pass

    def process(self, root_module: ModuleType) -> ApiCollection:
        res = ApiCollection()
        res.manifest.rootModule = root_module.__name__

        self.root_module = root_module
        self.mapper: dict[str, ApiEntry] = {}

        self.empty_entry = SpecialEntry(name="$empty$", kind=SpecialKind.Empty)
        self.external_entry = SpecialEntry(
            name="$external$", kind=SpecialKind.External)
        self.add_entry(self.empty_entry)
        self.add_entry(self.external_entry)

        root_entry = self.visit_module(self.root_module)

        for v in self.mapper.values():
            v.id = v.name
            res.addEntry(v)

        res.manifest.rootModule = root_entry.name

        srcpath = os.path.split(root_module.__file__)[0]

        return res


    def add_entry(self, entry: ApiEntry):
        if entry.name in self.mapper:
            raise Exception(f"Name {entry.name} has existed.")
        self.mapper[entry.name] = entry

    def visit_module(self, mod) -> ModuleEntry:
        assert inspect.ismodule(mod)

        modname = mod.__name__

        if modname in self.mapper:
            return cast(ModuleEntry, self.mapper[modname])

        res = ModuleEntry(name=modname)
        self.add_entry(res)

        for name, obj in inspect.getmembers(mod):
            entry = None
            if hasattr(obj, "__module__") and obj.__module__ and not obj.__module__.startswith(self.root_module.__name__):  # fix deep import
                entry = self.external_entry
            elif inspect.ismodule(obj):
                if obj.__name__.startswith(self.root_module.__name__):
                    entry = self.visit_module(obj)
                else:
                    entry = self.external_entry
            elif inspect.isclass(obj):
                entry = self.visit_class(obj)
            elif inspect.isfunction(obj):
                entry = self.visit_func(obj)
            else:
                entry = self.visit_field(obj, f"{modname}.{name}")
            res.members[name] = entry.name
        return res

    def visit_class(self, clas) -> ClassEntry:
        assert inspect.isclass(clas)

        qualname = _qualname(clas)

        if qualname in self.mapper:
            return cast(ClassEntry, self.mapper[qualname])

        res = ClassEntry(name=qualname,
                         bases=[_qualname(b) for b in clas.__bases__])
        self.add_entry(res)

        for name, obj in inspect.getmembers(clas):
            entry = None
            qname = _qualname(obj, f"{qualname}.{name}")
            if not qname.startswith(self.root_module.__name__):
                entry = self.external_entry
            elif inspect.isfunction(obj):
                entry = self.visit_func(obj)
            else:
                entry = self.visit_field(obj, qname)
            res.members[name] = entry.name

        return res

    def visit_func(self, func) -> FunctionEntry:
        assert inspect.isfunction(func)

        qualname = _qualname(func)
        if qualname in self.mapper:
            return cast(FunctionEntry, self.mapper[qualname])

        res = FunctionEntry(name=qualname)
        self.add_entry(res)

        try:
            sign = inspect.signature(func)

            if sign.return_annotation != inspect.Signature.empty:
                res.returnType = str(sign.return_annotation)

            for name, para in sign.parameters.items():
                paraEntry = Parameter(name=para.name)
                if para.default != inspect.Parameter.empty:
                    paraEntry.default = str(para.default)
                    paraEntry.optional = True
                if para.annotation != inspect.Parameter.empty:
                    paraEntry.type = str(para.annotation)
                paraEntry.kind = PARA_KIND_MAP[para.kind]
                res.parameters.append(paraEntry)
        except Exception as ex:
            self._logger.warning(f"Failed to analyze function {qualname}.")
            self._logger.warning(str(ex))

        return res

    def visit_field(self, field, default_name: str) -> FieldEntry:
        qualname = _qualname(field, default_name)

        if qualname in self.mapper:
            return cast(FieldEntry, self.mapper[qualname])

        res = FieldEntry(name=qualname, type=str(type(field)))
        self.add_entry(res)
        return res
