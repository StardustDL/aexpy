from datetime import datetime
import logging
import pathlib
from typing import Tuple


import mypy
from mypy import find_sources
from mypy.build import State
from mypy.version import __version__
from mypy.dmypy_util import DEFAULT_STATUS_FILE
from mypy.dmypy_server import Server
from mypy.options import Options
from mypy.nodes import (
    ARG_POS, ARG_STAR, ARG_NAMED, ARG_STAR2, ARG_NAMED_OPT, FuncDef, MypyFile, SymbolTable,
    SymbolNode, TypeInfo, Node, Expression, ReturnStmt, NameExpr, SymbolTableNode, Var,
    AssignmentStmt, Context, RefExpr, FuncBase, MemberExpr, CallExpr
)
from mypy.types import (
    Type, AnyType, TypeOfAny, CallableType, UnionType, NoneTyp, Instance, is_optional,
)
from mypy.traverser import TraverserVisitor
from mypy.infer import infer_function_type_arguments

from aexpy.analyses.models import ApiEntry, ClassEntry, ModuleEntry


class MypyServer:
    _logger = logging.getLogger("mypy")

    def __init__(self, sources: list[pathlib.Path]) -> None:
        self.options = Options()
        self.files = find_sources.create_source_list(sources, self.options)
        self._logger.debug(f"Mypy sources: {self.files}")
        self.server = Server(self.options, DEFAULT_STATUS_FILE)

    def prepare(self) -> None:
        self._logger.info(f"Start mypy checking {datetime.now()}.")
        result = self.server.check(self.files, False, 0)
        # if self.server.fine_grained_manager is None and result["status"] == 2: # Compile Error
        #     for line in result["out"].splitlines():
        #         try:
        #             file = pathlib.Path(line.split(":")[0]).absolute().as_posix()
        #             filt = [f for f in self.files if pathlib.Path(f.path).as_posix() == str(file)]
        #             if len(filt) > 0:
        #                 self.files.remove(filt[0])
        #                 self._logger.info(f"Remove compiled failed file: {filt[0].path} ({line})")
        #         except:
        #             pass
        #     result = self.server.check(self.files, False, 0)

        self._logger.info(f"Finish mypy checking {datetime.now()}: {result}")
        self.graph = self.server.fine_grained_manager.graph

    def module(self, file: pathlib.Path) -> State | None:
        file = file.absolute().as_posix()
        for v in self.graph.values():
            if pathlib.Path(v.abspath).absolute().as_posix() == file:
                return v

    def locals(self, module: State) -> dict[str, Tuple[SymbolTableNode, TypeInfo | None]]:
        return {k: (node, typeInfo)
                for k, node, typeInfo in module.tree.local_definitions()}


class PackageMypyServer:
    def __init__(self, unpacked: pathlib.Path, paths: list[pathlib.Path]) -> None:
        self.unpacked = unpacked
        self.proxy = MypyServer(paths)

    def prepare(self) -> None:
        self.cacheFile = {}
        self.cacheMembers = {}
        self.cacheElement = {}
        self.proxy.prepare()

    def file(self, entry: ApiEntry) -> State | None:
        if entry.location.file not in self.cacheFile:
            self.cacheFile[entry.location.file] = self.proxy.module(
                self.unpacked.joinpath(entry.location.file))
        return self.cacheFile[entry.location.file]

    def members(self, entry: ClassEntry) -> dict[str, SymbolTableNode]:
        if entry.id not in self.cacheMembers:
            mod = self.file(entry)

            result = {}

            if mod:
                for node, info in self.proxy.locals(mod).values():
                    if info is None:
                        continue
                    if node.fullname.startswith(entry.id) and info.fullname == entry.id:
                        result[node.fullname.replace(entry.id, "", 1).lstrip(".")] = node

            self.cacheMembers[entry.id] = result
        return self.cacheMembers[entry.id]

    def element(self, entry: ApiEntry) -> State | Tuple[SymbolTableNode, TypeInfo | None] | None:
        if entry.id not in self.cacheElement:
            result = None
            mod = self.file(entry)
            if isinstance(entry, ModuleEntry):
                result = mod
            elif mod:
                result = self.proxy.locals(mod).get(entry.id)
            self.cacheElement[entry.id] = result
        return self.cacheElement[entry.id]
