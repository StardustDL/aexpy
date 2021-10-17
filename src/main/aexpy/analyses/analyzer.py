from email.message import Message
import pathlib
from typing import Dict, List, Optional, Set, cast
from .models import ApiCollection, ApiEntry, FunctionEntry, FieldEntry, Location, ModuleEntry, ClassEntry, Parameter, ParameterKind, SpecialEntry, SpecialKind
from uuid import uuid1
from types import ModuleType
import inspect
import os
import logging
import ast
import shutil
import wheel.metadata
from . import UNPACKED_Dir

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

    def process(self, root_module: ModuleType) -> ApiCollection:
        res = ApiCollection()
        
        res.manifest.rootModule = root_module.__name__
        distInfo = self._getDistInfo()
        if distInfo:
            res.manifest.project = distInfo.get("name").strip()
            res.manifest.version = distInfo.get("version").strip()
            res.manifest.python = distInfo.get("requires-python").strip()
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

        for v in self.mapper.values():
            res.addEntry(v)

        res.manifest.rootModule = root_entry.name

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

        if isinstance(result, FieldEntry):
            return

        module = inspect.getmodule(obj)
        if module:
            result.location.module = module.__name__
        file = inspect.getfile(obj)
        if not file.startswith(str(self.rootPath)) and module:
            file = inspect.getfile(module)
        if file.startswith(str(self.rootPath)):
            result.location.file = str(pathlib.Path(
                file).relative_to(self.rootPath.parent))
        try:
            sl = inspect.getsourcelines(obj)
            src = "".join(sl[0])
            # remove indent
            result.src = inspect.cleandoc(src) if src.startswith(" ") else src
            result.location.line = sl[1]
        except:
            pass
        result.doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        result.comments = inspect.getcomments(obj) or ""

    def _is_external(self, obj) -> bool:
        module = inspect.getmodule(obj)
        if module:
            return not module.__name__.startswith(self.root_module.__name__)
        if inspect.ismodule(obj) or inspect.isclass(obj) or inspect.isfunction(obj):
            return not inspect.getfile(obj).startswith(str(self.rootPath))
        return False

    def visit_module(self, obj) -> ModuleEntry:
        assert inspect.ismodule(obj)

        id = self._get_id(obj)

        if id in self.mapper:
            return cast(ModuleEntry, self.mapper[id])

        res = ModuleEntry(id=id)
        self._visit_entry(res, obj)
        self.add_entry(res)

        for mname, member in inspect.getmembers(obj):
            entry = None
            if self._is_external(member):
                entry = self.external_entry
            elif inspect.ismodule(member):
                entry = self.visit_module(member)
            elif inspect.isclass(member):
                entry = self.visit_class(member)
            elif inspect.isfunction(member):
                entry = self.visit_func(member)
            else:
                entry = self.visit_field(
                    member, f"{id}.{mname}", res.location)
            res.members[mname] = entry.id
        return res

    def visit_class(self, obj) -> ClassEntry:
        assert inspect.isclass(obj)

        id = self._get_id(obj)

        if id in self.mapper:
            return cast(ClassEntry, self.mapper[id])

        res = ClassEntry(id=id,
                         bases=[b.__qualname__ for b in obj.__bases__])
        self._visit_entry(res, obj)
        self.add_entry(res)

        for mname, member in inspect.getmembers(obj):
            entry = None
            if self._is_external(member):
                entry = self.external_entry
            elif inspect.isfunction(member):
                entry = self.visit_func(member)
            else:
                entry = self.visit_field(
                    member, f"{id}.{mname}", res.location)
            res.members[mname] = entry.id

        return res

    def visit_func(self, obj) -> FunctionEntry:
        assert inspect.isfunction(obj)

        id = self._get_id(obj)

        if id in self.mapper:
            return cast(FunctionEntry, self.mapper[id])

        res = FunctionEntry(id=id)
        self._visit_entry(res, obj)
        self.add_entry(res)

        try:
            sign = inspect.signature(obj)

            if sign.return_annotation != inspect.Signature.empty:
                res.returnType = str(sign.return_annotation)

            for paraname, para in sign.parameters.items():
                paraEntry = Parameter(name=para.name)
                if para.default != inspect.Parameter.empty:
                    paraEntry.optional = True
                    if isinstance(para.default, bool):
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

                if para.annotation != inspect.Parameter.empty:
                    paraEntry.type = str(para.annotation)
                paraEntry.kind = PARA_KIND_MAP[para.kind]
                res.parameters.append(paraEntry)
        except Exception as ex:
            self._logger.warning(f"Failed to analyze function {id}.")
            self._logger.warning(str(ex))

        return res

    def visit_field(self, field, id: str, location: Optional[Location] = None) -> FieldEntry:
        if id in self.mapper:
            return cast(FieldEntry, self.mapper[id])

        res = FieldEntry(id=id, type=str(type(field)))

        self._visit_entry(res, field)

        if location:
            res.location = location
        self.add_entry(res)
        return res
