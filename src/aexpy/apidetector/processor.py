import inspect
import logging
import pathlib
from dataclasses import is_dataclass
from types import ModuleType
from typing import Any

from .abcs import buildBuiltinABCs
from .compat import (ApiEntry, AttributeEntry, ClassEntry, ClassFlag,
                     CollectionEntry, FunctionEntry, FunctionFlag, ItemScope,
                     Location, ModuleEntry, Parameter, ParameterKind,
                     SpecialEntry, getModuleName, getObjectId, isFunction,
                     isLocal)
from .ignores import isIgnoredMember


def getAnnotations(obj) -> "list[tuple[str, Any]]":
    if hasattr(inspect, "get_annotations"):
        return list(inspect.get_annotations(obj).items())
    return list(getattr(obj, "__annotations__", {}).items())


def getFile(obj) -> "str | None":
    return getattr(obj, "__file__", None)


def isFinal(obj):
    return bool(getattr(obj, "__final__", False))


def isOverride(obj):
    return bool(getattr(obj, "__override__", False))


def isAbstractMethod(obj):
    return bool(getattr(obj, "__isabstractmethod__", False))


def isGeneric(obj):
    return bool(getattr(obj, "__type_params__", False))


def isDeprecated(obj):
    return hasattr(obj, "__deprecated__")


class Processor:
    PARA_KIND_MAP = {
        inspect.Parameter.KEYWORD_ONLY: ParameterKind.Keyword,
        inspect.Parameter.VAR_KEYWORD: ParameterKind.VarKeyword,
        inspect.Parameter.VAR_POSITIONAL: ParameterKind.VarPositional,
        inspect.Parameter.POSITIONAL_ONLY: ParameterKind.Positional,
        inspect.Parameter.POSITIONAL_OR_KEYWORD: ParameterKind.PositionalOrKeyword,
    }

    def __init__(self, /):
        self.mapper: "dict[str, ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry]" = ({})
        self.logger = logging.getLogger("processor")
        self.abcs = buildBuiltinABCs(self.logger)

    def getObjectId(self, /, obj):
        try:
            return getObjectId(obj)
        except Exception:
            self.logger.error(f"Failed to get id.", exc_info=True)
            return "<unknown>"

    def process(self, /, root: ModuleType, others: "list[ModuleType]"):
        self.modules = others + [root]
        self.root = root
        rootFile = getFile(root)
        if rootFile:
            self.rootPath = pathlib.Path(rootFile).parent.resolve()
        else:
            self.rootPath = None

        self.visitModule(self.root)

        for module in others:
            if module == root:
                continue
            try:
                self.visitModule(module)
            except Exception:
                self.logger.error(f"Failed to visit module {module}.", exc_info=True)

    def allEntries(self, /):
        return list(self.mapper.values())

    def addEntry(
        self,
        /,
        entry: "ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry",
    ):
        if entry.id in self.mapper:
            raise Exception(f"Id {entry.id} has existed.")
        self.mapper[entry.id] = entry

    def _visitEntry(
        self,
        /,
        result: "ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry",
        obj,
    ):
        if "." in result.id:
            result.name = result.id.rsplit(".", maxsplit=1)[1]
        else:
            result.name = result.id

        try:
            result.deprecated = isDeprecated(obj)
            result.data["raw"] = repr(obj)
            result.data["dir"] = dir(obj)

            if isinstance(result, AttributeEntry):
                return

            if isinstance(result, CollectionEntry) or isinstance(result, FunctionEntry):
                try:
                    result.annotations = {k: str(v) for k, v in getAnnotations(obj)}
                except Exception:
                    self.logger.error(
                        f"Failed to get annotations by inspect of {result.id}.",
                        exc_info=True,
                    )

            location = Location()

            location.module = getModuleName(obj)

            module = inspect.getmodule(obj)

            try:
                file = inspect.getfile(obj)
                if self.rootPath:
                    if not file.startswith(str(self.rootPath)) and module:
                        file = inspect.getfile(module)
                    if file.startswith(str(self.rootPath)):
                        location.file = str(
                            pathlib.Path(file).relative_to(self.rootPath.parent)
                        )
            except Exception:
                self.logger.error(
                    f"Failed to get location for {result.id}", exc_info=True
                )

            try:
                sl = inspect.getsourcelines(obj)
                src = "".join(sl[0])
                result.src = src
                location.line = sl[1]
            except Exception:
                self.logger.error(
                    f"Failed to get source code for {result.id}", exc_info=True
                )
            result.docs = inspect.cleandoc(inspect.getdoc(obj) or "")
            result.comments = inspect.getcomments(obj) or ""
            result.location = location
        except Exception:
            self.logger.error(f"Failed to inspect entry for {result.id}", exc_info=True)

    def isExternal(self, /, obj):
        try:
            moduleName = getModuleName(obj)
            for module in self.modules:
                if moduleName:
                    return not moduleName.startswith(module.__name__)
                if inspect.ismodule(obj) or inspect.isclass(obj) or isFunction(obj):
                    moduleFile = getFile(module)
                    if moduleFile is None:
                        return True
                    try:
                        modulePath = str(pathlib.Path(moduleFile).parent.resolve())
                        return not str(
                            pathlib.Path(inspect.getfile(obj)).resolve()
                        ).startswith(modulePath)
                    except:
                        return True  # fail to get file -> a builtin module
        except:
            pass
        return False

    def visitModule(self, /, obj, parent: str = ""):
        assert inspect.ismodule(obj)

        id = self.getObjectId(obj)

        if id in self.mapper:
            res = self.mapper[id]
            assert isinstance(res, ModuleEntry)
            return res

        self.logger.debug(f"Module: {id}")

        res = ModuleEntry(id=id, parent=id.rsplit(".", 1)[0] if "." in id else parent)
        self._visitEntry(res, obj)
        self.addEntry(res)

        publicMembers = getattr(obj, "__all__", None)
        res.slots = {str(s) for s in (publicMembers or [])}

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                if isIgnoredMember(mname):
                    pass
                elif self.isExternal(member):
                    entry = self.getObjectId(member)
                elif inspect.ismodule(member):
                    entry = self.visitModule(member, parent=res.id)
                elif inspect.isclass(member):
                    entry = self.visitClass(member, parent=res.id)
                elif isFunction(member):
                    entry = self.visitFunc(member, parent=res.id)
                else:
                    entry = self.visitAttribute(
                        member,
                        f"{id}.{mname}",
                        res.annotations.get(mname) or "",
                        res.location,
                        parent=res.id,
                    )
                    if not entry.annotation:
                        entry.annotation = res.annotations.get(mname) or ""
                if (
                    publicMembers is not None
                    and isinstance(entry, ApiEntry)
                    and entry.parent == res.id
                ):
                    entry.private = mname not in publicMembers
            except Exception:
                self.logger.error(
                    f"Failed to extract module member {id}.{mname}: {member}",
                    exc_info=True,
                )
            if isinstance(entry, ApiEntry):
                res.members[mname] = entry.id
            elif isinstance(entry, str):
                res.members[mname] = entry
        return res

    def visitClass(self, /, obj, parent: str = ""):
        assert inspect.isclass(obj)

        id = self.getObjectId(obj)

        if id in self.mapper:
            res = self.mapper[id]
            assert isinstance(res, ClassEntry)
            return res

        self.logger.debug(f"Class: {id}")

        bases = obj.__bases__

        istuple = tuple in bases

        abcs = []

        for abc in self.abcs:
            if issubclass(obj, abc):
                abcs.append(self.getObjectId(abc))

        res = ClassEntry(
            id=id,
            bases=[self.getObjectId(b) for b in bases],
            abcs=abcs,
            mros=[self.getObjectId(b) for b in inspect.getmro(obj)],
            slots={str(s) for s in getattr(obj, "__slots__", [])},
            parent=id.rsplit(".", 1)[0] if "." in id else parent,
            flags=(ClassFlag.Abstract if inspect.isabstract(obj) else ClassFlag.Empty)
            | (ClassFlag.Final if isFinal(obj) else ClassFlag.Empty)
            | (ClassFlag.Generic if isGeneric(obj) else ClassFlag.Empty)
            | (ClassFlag.Dataclass if is_dataclass(obj) else ClassFlag.Empty),
        )
        self._visitEntry(res, obj)
        self.addEntry(res)

        slots = set(res.slots)

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                # ignore parent
                if member is not None and any(
                    (base for base in bases if member is getattr(base, mname, None))
                ):
                    pass
                elif isIgnoredMember(mname):
                    pass
                elif not (istuple and mname == "__new__") and self.isExternal(member):
                    entry = self.getObjectId(member)
                elif inspect.ismodule(member):
                    entry = self.visitModule(member, parent=res.id)
                elif inspect.isclass(member):
                    entry = self.visitClass(member, parent=res.id)
                elif isFunction(member):
                    if (
                        istuple and mname == "__new__"
                    ):  # named tuple class will have a special new method that default __module__ is a generated value
                        entry = self.visitFunc(
                            member, f"{id}.{mname}", res.location, parent=res.id
                        )
                    else:
                        tid = self.getObjectId(member)
                        if (
                            ClassFlag.Dataclass in res.flags
                            and mname
                            in (
                                "__eq__",
                                "__lt__",
                                "__le__",
                                "__gt__",
                                "__ge__",
                                "__hash__",
                                "__init__",
                                "__repr__",
                                "__setattr__",
                                "__delattr__",
                            )
                            and isLocal(tid)
                        ):
                            # dataclass has auto-generated methods, and has same qualname (a bug in cpython https://bugs.python.org/issue41747)
                            entry = self.visitFunc(
                                member, f"{id}.{mname}", parent=res.id
                            )
                        else:
                            entry = self.visitFunc(member, parent=res.id)
                    if inspect.ismethod(member):
                        entry.scope = ItemScope.Class
                    if len(entry.parameters) > 0:
                        if entry.parameters[0].name == "self":
                            entry.scope = ItemScope.Instance
                        # elif entry.parameters[0].name == "cls":
                        #     entry.scope = ItemScope.Class
                else:
                    entry = self.visitAttribute(
                        member,
                        f"{id}.{mname}",
                        res.annotations.get(mname) or "",
                        res.location,
                        parent=res.id,
                    )
                    if not entry.annotation:
                        entry.annotation = res.annotations.get(mname) or ""
                    if mname in slots:
                        entry.scope = ItemScope.Instance
            except Exception:
                self.logger.error(
                    f"Failed to extract class member {id}.{mname}: {member}",
                    exc_info=True,
                )
            if isinstance(entry, ApiEntry):
                res.members[mname] = entry.id
            elif isinstance(entry, str):
                res.members[mname] = entry

        return res

    def visitFunc(
        self,
        /,
        obj,
        id: str = "",
        location: "Location | None" = None,
        parent: str = "",
    ):
        assert isFunction(obj)

        if not id:
            id = self.getObjectId(obj)

        if id in self.mapper:
            res = self.mapper[id]
            assert isinstance(res, FunctionEntry)
            return res

        self.logger.debug(f"Function: {id}")

        res = FunctionEntry(
            id=id,
            parent=id.rsplit(".", 1)[0] if "." in id else parent,
            flags=(
                FunctionFlag.Abstract if isAbstractMethod(obj) else FunctionFlag.Empty
            )
            | (FunctionFlag.Final if isFinal(obj) else FunctionFlag.Empty)
            | (FunctionFlag.Generic if isGeneric(obj) else FunctionFlag.Empty)
            | (FunctionFlag.Override if isOverride(obj) else FunctionFlag.Empty)
            | (
                FunctionFlag.Async
                if inspect.iscoroutinefunction(obj)
                else FunctionFlag.Empty
            ),
        )

        if location and not res.location:
            res.location = location

        self._visitEntry(res, obj)
        self.addEntry(res)

        try:
            sign = inspect.signature(obj)

            if sign.return_annotation != inspect.Signature.empty:
                res.returnAnnotation = str(sign.return_annotation)

            for paraname, para in sign.parameters.items():
                paraEntry = Parameter(name=para.name, source=res.id)
                if para.default != inspect.Parameter.empty:
                    paraEntry.optional = True
                    if para.default is None:
                        paraEntry.default = "None"
                    elif isinstance(
                        para.default, (bool, int, float, complex, str, bytes, tuple)
                    ):
                        paraEntry.default = (
                            f"{para.default.__class__.__name__}('{str(para.default)}')"
                        )
                    else:  # variable default value
                        paraEntry.default = None

                if para.annotation != inspect.Parameter.empty:
                    paraEntry.annotation = str(para.annotation)
                paraEntry.kind = self.PARA_KIND_MAP[para.kind]
                res.parameters.append(paraEntry)
        except Exception:
            self.logger.error(
                f"Failed to extract function signature {id}.", exc_info=True
            )

        return res

    def visitAttribute(
        self,
        /,
        attribute,
        id: str,
        annotation: str = "",
        location: "Location | None" = None,
        parent: str = "",
    ):
        if id in self.mapper:
            res = self.mapper[id]
            assert isinstance(res, AttributeEntry)
            return res

        self.logger.debug(f"Attribute: {id}")

        res = AttributeEntry(
            id=id,
            rawType=str(type(attribute)),
            annotation=annotation,
            parent=id.rsplit(".", 1)[0] if "." in id else parent,
        )

        self._visitEntry(res, attribute)

        if location and not res.location:
            res.location = location

        res.property = isinstance(attribute, property)

        self.addEntry(res)
        return res
