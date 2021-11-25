from typing import Callable
from aexpy.analyses.models import ApiCollection, ApiManifest, ApiEntry, ModuleEntry, FunctionEntry, AttributeEntry, ClassEntry
from aexpy.logging.models import PayloadLog

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

    from aexpy.analyses.enriching.callgraph.type import TypeCallgraphBuilder
    from aexpy.analyses.enriching.callgraph.basic import BasicCallgraphBuilder


# put your codes here

version = api.manifest.version


info = AnalysisInfo(wheel=pathlib.Path(rf"D:\Program\aexpy\src\main\cache\wheels\schemdule-{version}-py3-none-any.whl"),
                    unpacked=pathlib.Path(
                        rf"D:\Program\aexpy\src\main\cache\wheels\unpacked\schemdule-{version}-py3-none-any"),
                    distinfo=DistInfo(Message(), ["schemdule"], Message()), cache=None, log=None)

server = PackageMypyServer(info.unpacked, info.src())
server.prepare()

cgold = BasicCallgraphBuilder().build(api)
cg = TypeCallgraphBuilder(server).build(api)

# print("OLD")

# for name, caller in cgold.items.items():
#     targets = []
#     for i, site in enumerate(caller.sites):
#         # print(f"  {i}. {site.targets}")
#         targets.extend(site.targets)
#     if targets:
#         print(name, targets)

# print("NEW")

def filt(targets):
    return [target for target in targets if isinstance(api.entries.get(target), FunctionEntry)]

for name, caller in cg.items.items():
    oldtargets = []
    for i, site in enumerate(cgold.items[name].sites):
        oldtargets.extend(site.targets)
    targets = []
    for i, site in enumerate(caller.sites):
        # print(f"  {i}. {site.targets}")
        targets.extend(site.targets)
    oldtargets = filt(oldtargets)
    targets = filt(targets)
    if oldtargets or targets:
        print(name)
        print(" ", oldtargets)
        print(" ", targets)

# for name, caller in cg.items.items():
#     print(name)
#     oldcaller = cgold.items[name]
#     for i, site in enumerate(caller.sites):
#         oldsite = oldcaller.sites[i]
#         if site.targets or oldsite.targets:
#             print(f"  {oldsite.targets} -> {site.targets}")

# code.interact(local={
#     **locals()
# })
