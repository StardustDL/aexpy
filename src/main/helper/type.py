import code
from aexpy.logging.models import PayloadLog
from aexpy.downloads.wheels import DistInfo
from aexpy.analyses.models import ApiCollection, ApiManifest, ApiEntry, ModuleEntry, FunctionEntry, AttributeEntry, ClassEntry
from typing import Callable
import pathlib
from email.message import Message
import ast
import logging
from ast import NodeVisitor
from dataclasses import Field, asdict
import mypy
from mypy import find_sources
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
from aexpy.analyses.models import (ApiCollection, ApiEntry, AttributeEntry, ClassEntry, FunctionEntry,
                                   Parameter, ParameterKind)
from aexpy.analyses.enriching import AnalysisInfo, Enricher, callgraph, clearSrc
from mypy.build import Graph, State
from os import PathLike

api: ApiCollection = ApiCollection
A: ApiCollection = api
manifest: ApiManifest = api.manifest
entries: dict[str, ApiEntry] = {}
E: dict[str, ApiEntry] = {}
EL: list[ApiEntry] = []
names: dict[str, list[ApiEntry]] = {}
N: dict[str, list[ApiEntry]] = {}
M: dict[str, ModuleEntry] = {}
C: dict[str, ClassEntry] = {}
F: dict[str, FunctionEntry] = {}
P: dict[str, AttributeEntry] = {}
ML: list[ModuleEntry] = []
CL: list[ClassEntry] = []
FL: list[FunctionEntry] = []
PL: list[AttributeEntry] = []
log: PayloadLog = PayloadLog()
read: Callable[[str | ApiEntry], None] = lambda item: None
# START
if True:
    import code
    from aexpy.logging.models import PayloadLog
    from aexpy.downloads.wheels import DistInfo
    from aexpy.analyses.models import ApiCollection, ApiManifest, ApiEntry, ModuleEntry, FunctionEntry, AttributeEntry, ClassEntry
    from typing import Callable
    import pathlib
    from email.message import Message
    import ast
    import logging
    from ast import NodeVisitor
    from dataclasses import Field, asdict
    import mypy
    from mypy import find_sources
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
    from aexpy.analyses.models import (ApiCollection, ApiEntry, AttributeEntry, ClassEntry, FunctionEntry,
                                       Parameter, ParameterKind)
    from aexpy.analyses.enriching import AnalysisInfo, Enricher, callgraph, clearSrc
    from mypy.build import Graph, State
    from os import PathLike

    from aexpy.analyses.enriching.mypyserver import PackageMypyServer

# put your codes here


class TypeEnricher(Enricher):
    def __init__(self, server: PackageMypyServer) -> None:
        super().__init__()
        self.server = server

    def enrich(self, api: ApiCollection, logger: logging.Logger | None = None) -> None:
        self.logger = logger if logger is not None else logging.getLogger(
            "type-enrich")
        


info = AnalysisInfo(wheel=pathlib.Path(r"D:\Program\aexpy\src\main\cache\wheels\click-8.0.1-py3-none-any.whl"),
                    unpacked=pathlib.Path(
                        r"D:\Program\aexpy\src\main\cache\wheels\unpacked\click-8.0.1-py3-none-any"),
                    distinfo=DistInfo(Message(), "click", Message()), cache=None, log=None)

server = PackageMypyServer(info.unpacked, info.distinfo.topLevel)
server.prepare()

R = TypeEnricher(server)

R.enrich(api, info)

print(R.server.members(CL[0]))

code.interact(local={
    **locals()
})

# for item in R.files:
# print(item.path)

# file's attributes:
# dependencies
# ancestors
# tree

# tree's attributes:
# accept()
# fullname
# imports
# is_package_init_file
# is_partial_stub_package
# is_stub
# local_definitions() -> generator[name: SymbolTableNode, TypeInfo]
# names
# name
# path

# SymbolTableNode's attributes
# cross_ref
# fullname
# node: ast node
# module_hidden
# module_public
# kind
# implicit
