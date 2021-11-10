import ast
import inspect
import logging
import os
import pathlib
import shutil
import textwrap
from email.message import Message
from types import ModuleType
from typing import Dict, List, Optional, Set, cast
from uuid import uuid1

import wheel.metadata

from . import UNPACKED_Dir
from .models import (ApiCollection, ApiEntry, ClassEntry, AttributeEntry, CollectionEntry,
                     FunctionEntry, Location, ModuleEntry, Parameter,
                     ParameterKind, SpecialEntry, SpecialKind)

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

    def _getDistInfo(self) -> Optional[Message]:
        distinfoDir = list(UNPACKED_Dir.glob("*.dist-info"))
        if len(distinfoDir) == 0:
            return None
        distinfoDir = distinfoDir[0]
        return wheel.metadata.read_pkg_info(distinfoDir.joinpath("METADATA"))

    def process(self, root_module: ModuleType, modules: List[ModuleType]) -> ApiCollection:
        res = ApiCollection()

        distInfo = self._getDistInfo()
        if distInfo:
            res.manifest.project = distInfo.get("name", "").strip()
            res.manifest.version = distInfo.get("version", "").strip()
        else:
            res.manifest.project = "Unknown"
            res.manifest.version = "Unknown"        

        self.root_module = root_module
        self.rootPath = pathlib.Path(root_module.__file__).parent.absolute()
        self.mapper: dict[str, ApiEntry] = {}

        self.empty_entry = SpecialEntry(id="$empty$", kind=SpecialKind.Empty)
        self.external_entry = SpecialEntry(
            id="$external$", kind=SpecialKind.External)
        self.add_entry(self.empty_entry)
        self.add_entry(self.external_entry)

        root_entry = self.visit_module(self.root_module)

        for module in modules:
            if module == root_module:
                continue
            try:
                self.visit_module(module)
            except Exception as ex:
                self._logger.error(ex)

        for v in self.mapper.values():
            res.addEntry(v)

        res.manifest.topLevel = root_entry.name

        return res

    def add_entry(self, entry: ApiEntry):
        if entry.id in self.mapper:
            raise Exception(f"Id {entry.id} has existed.")
        self.mapper[entry.id] = entry

    def _get_id(self, obj) -> str:
        if inspect.ismodule(obj):
            return obj.__name__

        module = inspect.getmodule(obj)
        if module:
            return f"{module.__name__}.{obj.__qualname__}"
        else:
            return obj.__qualname__

    def _visit_entry(self, result: ApiEntry, obj) -> None:
        if "." in result.id:
            result.name = result.id.split('.')[-1]
        else:
            result.name = result.id

        if isinstance(result, AttributeEntry):
            return

        if isinstance(result, CollectionEntry) or isinstance(result, FunctionEntry):
            # result.annotations = { k: str(v) for k, v in inspect.get_annotations(obj).items()}
            annotations = getattr(obj, "__annotations__", {})
            result.annotations = { k: str(v) for k, v in annotations.items()}

        module = inspect.getmodule(obj)
        if module:
            result.location.module = module.__name__

        try:
            file = inspect.getfile(obj)
            if not file.startswith(str(self.rootPath)) and module:
                file = inspect.getfile(module)
            if file.startswith(str(self.rootPath)):
                result.location.file = str(pathlib.Path(
                    file).relative_to(self.rootPath.parent))
        except:
            pass

        try:
            sl = inspect.getsourcelines(obj)
            src = "".join(sl[0])
            result.src = src
            result.location.line = sl[1]
        except:
            pass
        result.doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        result.comments = inspect.getcomments(obj) or ""

    def _is_external(self, obj) -> bool:
        try:
            module = inspect.getmodule(obj)
            if module:
                return not module.__name__.startswith(self.root_module.__name__)
            if inspect.ismodule(obj) or inspect.isclass(obj) or inspect.isfunction(obj):
                try:
                    return not inspect.getfile(obj).startswith(str(self.rootPath))
                except:
                    return True  # fail to get file -> a builtin module
        except:
            pass
        return False

    def visit_module(self, obj) -> ModuleEntry:
        assert inspect.ismodule(obj)

        id = self._get_id(obj)

        if id in self.mapper:
            return cast(ModuleEntry, self.mapper[id])

        self._logger.debug(f"Module: {id}")

        res = ModuleEntry(id=id)
        self._visit_entry(res, obj)
        self.add_entry(res)

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                if self._is_external(member):
                    entry = self.external_entry
                elif inspect.ismodule(member):
                    entry = self.visit_module(member)
                elif inspect.isclass(member):
                    entry = self.visit_class(member)
                elif inspect.isfunction(member):
                    entry = self.visit_func(member)
                else:
                    entry = self.visit_attribute(
                        member, f"{id}.{mname}", res.location)
            except Exception as ex:
                self._logger.error(ex)
            if entry:
                res.members[mname] = entry.id
        return res

    def visit_class(self, obj) -> ClassEntry:
        assert inspect.isclass(obj)

        id = self._get_id(obj)

        if id in self.mapper:
            return cast(ClassEntry, self.mapper[id])

        self._logger.debug(f"Class: {id}")

        res = ClassEntry(id=id,
                         bases=[self._get_id(b) for b in obj.__bases__],
                         mro=[self._get_id(b) for b in inspect.getmro(obj)])
        self._visit_entry(res, obj)
        self.add_entry(res)

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                if self._is_external(member):
                    entry = self.external_entry
                elif inspect.isfunction(member):
                    entry = self.visit_func(member)
                else:
                    entry = self.visit_attribute(
                        member, f"{id}.{mname}", res.location)
            except Exception as ex:
                self._logger.error(ex)
            if entry:
                res.members[mname] = entry.id

        return res

    def visit_func(self, obj) -> FunctionEntry:
        assert inspect.isfunction(obj)

        id = self._get_id(obj)

        if id in self.mapper:
            return cast(FunctionEntry, self.mapper[id])

        self._logger.debug(f"Function: {id}")

        res = FunctionEntry(id=id)
        self._visit_entry(res, obj)
        self.add_entry(res)

        try:
            sign = inspect.signature(obj)

            if sign.return_annotation != inspect.Signature.empty:
                res.returnAnnotation = str(sign.return_annotation)

            for paraname, para in sign.parameters.items():
                paraEntry = Parameter(name=para.name)
                if para.default != inspect.Parameter.empty:
                    paraEntry.optional = True
                    if para.default is True or para.default is False:
                        paraEntry.default = f"bool('{str(para.default)}')"
                    elif isinstance(para.default, int):
                        paraEntry.default = f"int('{str(para.default)}')"
                    elif isinstance(para.default, float):
                        paraEntry.default = f"float('{str(para.default)}')"
                    elif isinstance(para.default, str):
                        paraEntry.default = f"str('{str(para.default)}')"
                    elif para.default is None:
                        paraEntry.default = "None"
                    else:  # variable default value
                        paraEntry.default = None

                    """
                    match para.default:
                        case bool():
                            paraEntry.default = f"bool('{str(para.default)}')"
                        case int():
                            paraEntry.default = f"int('{str(para.default)}')"
                        case float():
                            paraEntry.default = f"float('{str(para.default)}')"
                        case str():
                            paraEntry.default = f"str('{str(para.default)}')"
                        case None:
                            paraEntry.default = "None"
                        case _: # variable default value
                            paraEntry.default = None
                    """

                if para.annotation != inspect.Parameter.empty:
                    paraEntry.annotation = str(para.annotation)
                paraEntry.kind = PARA_KIND_MAP[para.kind]
                res.parameters.append(paraEntry)
        except Exception as ex:
            self._logger.error(f"Failed to analyze function {id}.", exc_info=ex)

        return res

    def visit_attribute(self, attribute, id: str, location: Optional[Location] = None) -> AttributeEntry:
        if id in self.mapper:
            return cast(AttributeEntry, self.mapper[id])

        self._logger.debug(f"Attribute: {id}")

        res = AttributeEntry(id=id, type=str(type(attribute)))

        self._visit_entry(res, attribute)

        if location:
            res.location = location
        self.add_entry(res)
        return res
