import ast
import logging
from ast import NodeVisitor
from dataclasses import Field, asdict

from ..models import (ApiCollection, ApiEntry, AttributeEntry, ClassEntry, FunctionEntry,
                      Parameter, ParameterKind)
from . import Enricher, callgraph, clearSrc


class InstanceAttributeSetGetter(NodeVisitor):
    def __init__(self, target: FunctionEntry, logger: logging.Logger, parent: ClassEntry, api: ApiCollection) -> None:
        super().__init__()
        self.logger = logger
        self.target = target
        self.parent = parent
        self.api = api

    def add(self, name: str):
        if name in self.parent.members:
            return
        id=f"{self.parent.id}.{name}"
        entry = None
        if id in self.api.entries:
            entry = self.api.entries[id]
        else:
            entry = AttributeEntry(name=name, id=id, bound=True)
            self.api.addEntry(entry)
        self.parent.members[name] = id
        self.logger.debug(f"Detect attribute {entry.name}: {entry.id}")
    
    def getAttributeName(self, node) -> str | None:
        if not isinstance(node, ast.Attribute):
            return None
        if not isinstance(node.value, ast.Name):
            return None
        if node.value.id != "self":
            return None
        return node.attr
    
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            name = self.getAttributeName(target)
            if name:
                self.add(name)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        name = self.getAttributeName(node.target)
        if name:
            self.add(name)
    
    def visit_AugAssign(self, node: ast.AugAssign):
        name = self.getAttributeName(node.target)
        if name:
            self.add(name)



class InstanceAttributeEnricher(Enricher):
    def enrich(self, api: ApiCollection, logger: logging.Logger | None = None) -> None:
        self.logger = logger if logger is not None else logging.getLogger(
            "instance-attr-enrich")

        for cls in api.classes.values():
            self.enrichByFunctions(api, cls)
        

    def enrichByFunctions(self, api: ApiCollection, cls: ClassEntry) -> None:
        if "__slots__" in cls.members:
            # limit attribute names
            # done by dynamic member detecting
            return
        members = list(cls.members.items())
        for name, member in members:
            target = api.entries[member]
            if not isinstance(target, FunctionEntry):
                continue
            src = clearSrc(target.src)
            try:
                astree = ast.parse(src)
            except Exception as ex:
                self.logger.error(
                    f"Failed to parse code from {target.id}:\n{src}", exc_info=ex)
                continue
            InstanceAttributeSetGetter(target, self.logger, cls, api).visit(astree)