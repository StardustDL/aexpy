import ast
import logging
from ast import NodeVisitor
from typing import override

from ...models import ApiDescription
from ...models.description import (AttributeEntry, ClassEntry, FunctionEntry,
                                   ItemScope, isPrivate)
from ..third.mypyserver import PackageMypyServer
from . import Enricher, clearSrc


class InstanceAttributeAstAssignGetter(NodeVisitor):
    def __init__(
        self,
        /,
        target: FunctionEntry,
        logger: logging.Logger,
        parent: ClassEntry,
        api: ApiDescription,
    ) -> None:
        super().__init__()
        self.logger = logger
        self.target = target
        self.parent = parent
        self.api = api

    def add(self, /, name: str):
        if name in self.parent.members:
            return
        id = f"{self.parent.id}.{name}"
        entry = self.api[id]
        if entry is None:
            entry = AttributeEntry(
                name=name,
                id=id,
                scope=ItemScope.Instance,
                location=self.parent.location,
                parent=self.parent.id,
            )
            entry.private = isPrivate(entry)
            self.api.add(entry)
        self.parent.members[name] = id
        self.logger.debug(f"Detect attribute {entry.name}: {entry.id}")

    def getAttributeName(self, /, node) -> str | None:
        if not isinstance(node, ast.Attribute):
            return None
        if not isinstance(node.value, ast.Name):
            return None
        if node.value.id != "self":
            return None
        return node.attr

    @override
    def visit_Assign(self, /, node):
        for target in node.targets:
            name = self.getAttributeName(target)
            if name:
                self.add(name)
        super().generic_visit(node)

    @override
    def visit_AnnAssign(self, /, node):
        name = self.getAttributeName(node.target)
        if name:
            self.add(name)
        super().generic_visit(node)

    @override
    def visit_AugAssign(self, /, node):
        name = self.getAttributeName(node.target)
        if name:
            self.add(name)
        super().generic_visit(node)

    @override
    def visit_NamedExpr(self, /, node):
        name = self.getAttributeName(node.target)
        if name:
            self.add(name)
        super().generic_visit(node)


class InstanceAttributeAstEnricher(Enricher):
    def __init__(self, /, logger: logging.Logger | None = None):
        super().__init__()
        self.logger = (
            logger.getChild("instance-attr-ast-enrich")
            if logger is not None
            else logging.getLogger("instance-attr-ast-enrich")
        )

    @override
    def enrich(self, /, api):
        for cls in api.classes.values():
            self.enrichClass(api, cls)

    def enrichClass(self, /, api: ApiDescription, cls: ClassEntry):
        if cls.slots:
            # limit attribute names
            # done by dynamic member detecting
            return
        members = list(cls.members.items())
        for name, member in members:
            target = api[member]
            if not isinstance(target, FunctionEntry):
                continue
            src = clearSrc(target.src)
            try:
                astree = ast.parse(src)
            except Exception:
                self.logger.error(
                    f"Failed to parse code from {target.id}:\n{src}", exc_info=True
                )
                continue
            InstanceAttributeAstAssignGetter(target, self.logger, cls, api).visit(
                astree
            )


class InstanceAttributeMypyEnricher(Enricher):
    def __init__(
        self, /, server: PackageMypyServer, logger: logging.Logger | None = None
    ) -> None:
        super().__init__()
        self.server = server
        self.logger = (
            logger.getChild("instance-attr-mypy-enrich")
            if logger is not None
            else logging.getLogger("instance-attr-mypy-enrich")
        )

    @override
    def enrich(self, /, api):
        for cls in api.classes.values():
            self.enrichClass(api, cls)

    def enrichClass(self, /, api: ApiDescription, cls: ClassEntry):
        members = self.server.members(cls)
        for name, member in members.items():
            if not member.implicit:
                continue
            id = f"{cls.id}.{name}"
            entry = api[id]
            if entry is None:
                entry = AttributeEntry(
                    name=name,
                    id=id,
                    scope=ItemScope.Instance,
                    location=cls.location,
                    parent=cls.id,
                )
                entry.private = isPrivate(entry)
                api.add(entry)
            cls.members[name] = id
            self.logger.debug(f"Detect attribute {entry.name}: {entry.id}")
