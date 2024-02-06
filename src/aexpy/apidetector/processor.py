from dataclasses import is_dataclass
import inspect
import logging
import pathlib

# Builtin ABCs (https://docs.python.org/3/glossary.html#term-abstract-base-class)
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    ByteString,
    Callable,
    Collection,
    Container,
    Coroutine,
    Generator,
    Hashable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    MappingView,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Reversible,
    Sequence,
    Set,
    Sized,
    ValuesView,
)
from importlib.abc import (
    ExecutionLoader,
    FileLoader,
    InspectLoader,
    Loader,
    MetaPathFinder,
    PathEntryFinder,
    ResourceLoader,
    SourceLoader,
)
from io import BufferedIOBase, IOBase, RawIOBase, TextIOBase
from numbers import Complex, Integral, Rational, Real
from types import ModuleType
from typing import Any

from .compat import (
    ApiEntry,
    SpecialEntry,
    AttributeEntry,
    ClassEntry,
    CollectionEntry,
    FunctionEntry,
    ItemScope,
    Location,
    ModuleEntry,
    Parameter,
    ParameterKind,
)
from .compat import getObjectId, islocal, getModuleName, isFunction

ABCs = [
    Container,
    Hashable,
    Iterable,
    Iterator,
    Reversible,
    Generator,
    Sized,
    Callable,
    Collection,
    Sequence,
    MutableSequence,
    ByteString,
    Set,
    MutableSet,
    Mapping,
    MutableMapping,
    MappingView,
    ItemsView,
    KeysView,
    ValuesView,
    Awaitable,
    Coroutine,
    AsyncIterable,
    AsyncIterator,
    AsyncGenerator,
    Complex,
    Real,
    Rational,
    Integral,
    IOBase,
    RawIOBase,
    BufferedIOBase,
    TextIOBase,
    Loader,
    MetaPathFinder,
    PathEntryFinder,
    ResourceLoader,
    InspectLoader,
    ExecutionLoader,
    FileLoader,
    SourceLoader,
]


def getAnnotations(obj) -> "list[tuple[str, Any]]":
    if hasattr(inspect, "get_annotations"):
        return list(inspect.get_annotations(obj).items())
    return list(getattr(obj, "__annotations__", {}).items())


class Processor:
    PARA_KIND_MAP = {
        inspect.Parameter.KEYWORD_ONLY: ParameterKind.Keyword,
        inspect.Parameter.VAR_KEYWORD: ParameterKind.VarKeyword,
        inspect.Parameter.VAR_POSITIONAL: ParameterKind.VarPositional,
        inspect.Parameter.POSITIONAL_ONLY: ParameterKind.Positional,
        inspect.Parameter.POSITIONAL_OR_KEYWORD: ParameterKind.PositionalOrKeyword,
    }

    ignoredMember = {
        "__weakref__",
        "__dict__",
        "__annotations__",
        "__package__",
        "__builtins__",
        "__file__",
        "__name__",
        "__members__",
        "__slots__",
        "__bases__",
        "__mro__",
        "__cached__",
        "__all__",
        "__loader__",
        "__spec__",
        "__qualname__",
        "__doc__",
        "__path__",
        "__init_subclass__",
        "__module__",
        "__subclasshook__",
        "__abstractmethods__",
        "_abc_impl",
        "__match_args__",
        "__dataclass_params__",
        "__dataclass_fields__",
    }

    def __init__(self):
        self.mapper: "dict[str, ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry]" = (
            {}
        )
        self.logger = logging.getLogger("processor")

    def getObjectId(self, obj):
        try:
            return getObjectId(obj)
        except Exception as ex:
            self.logger.error(f"Failed to get id.", exc_info=ex)
            return "<unknown>"

    def process(self, root: ModuleType, others: "list[ModuleType]"):
        self.modules = others + [root]
        self.root = root
        assert root.__file__
        self.rootPath = pathlib.Path(root.__file__).parent.resolve()

        self.visitModule(self.root)

        for module in others:
            if module == root:
                continue
            try:
                self.visitModule(module)
            except Exception as ex:
                self.logger.error(f"Failed to visit module {module}.", exc_info=ex)

    def allEntries(self):
        return list(self.mapper.values())

    def addEntry(
        self,
        entry: "ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry",
    ):
        if entry.id in self.mapper:
            raise Exception(f"Id {entry.id} has existed.")
        self.mapper[entry.id] = entry

    def _visitEntry(
        self,
        result: "ModuleEntry | ClassEntry | FunctionEntry | AttributeEntry | SpecialEntry",
        obj,
    ):
        if "." in result.id:
            result.name = result.id.split(".")[-1]
        else:
            result.name = result.id

        try:
            result.data["raw"] = repr(obj)
            result.data["dir"] = dir(obj)

            if isinstance(result, AttributeEntry):
                return

            if isinstance(result, CollectionEntry) or isinstance(result, FunctionEntry):
                try:
                    result.annotations = {k: str(v) for k, v in getAnnotations(obj)}
                except Exception as ex:
                    self.logger.error(
                        f"Failed to get annotations by inspect of {result.id}.",
                        exc_info=ex,
                    )

            location = Location()

            location.module = getModuleName(obj)

            module = inspect.getmodule(obj)

            try:
                file = inspect.getfile(obj)
                if not file.startswith(str(self.rootPath)) and module:
                    file = inspect.getfile(module)
                if file.startswith(str(self.rootPath)):
                    location.file = str(
                        pathlib.Path(file).relative_to(self.rootPath.parent)
                    )
            except Exception as ex:
                self.logger.error(
                    f"Failed to get location for {result.id}", exc_info=ex
                )

            try:
                sl = inspect.getsourcelines(obj)
                src = "".join(sl[0])
                result.src = src
                location.line = sl[1]
            except Exception as ex:
                self.logger.error(
                    f"Failed to get source code for {result.id}", exc_info=ex
                )
            result.docs = inspect.cleandoc(inspect.getdoc(obj) or "")
            result.comments = inspect.getcomments(obj) or ""
            result.location = location
        except Exception as ex:
            self.logger.error(f"Failed to inspect entry for {result.id}", exc_info=ex)

    def isExternal(self, obj):
        try:
            moduleName = getModuleName(obj)
            for module in self.modules:
                if moduleName:
                    return not moduleName.startswith(module.__name__)
                if inspect.ismodule(obj) or inspect.isclass(obj) or isFunction(obj):
                    try:
                        modulePath = str(pathlib.Path(module.__file__).parent.resolve())
                        return not str(pathlib.Path(inspect.getfile(obj)).resolve()).startswith(modulePath)
                    except:
                        return True  # fail to get file -> a builtin module
        except:
            pass
        return False

    def visitModule(self, obj, parent: str = ""):
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

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                if mname in self.ignoredMember:
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
                if publicMembers is not None and isinstance(entry, ApiEntry):
                    entry.private = mname in publicMembers
            except Exception as ex:
                self.logger.error(
                    f"Failed to extract module member {id}.{mname}: {member}",
                    exc_info=ex,
                )
            if isinstance(entry, ApiEntry):
                res.members[mname] = entry.id
            elif isinstance(entry, str):
                res.members[mname] = entry
        return res

    def visitClass(self, obj, parent: str = ""):
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

        for abc in ABCs:
            if issubclass(obj, abc):
                abcs.append(self.getObjectId(abc))

        res = ClassEntry(
            id=id,
            bases=[self.getObjectId(b) for b in bases],
            abcs=abcs,
            mros=[self.getObjectId(b) for b in inspect.getmro(obj)],
            slots=[str(s) for s in getattr(obj, "__slots__", [])],
            parent=id.rsplit(".", 1)[0] if "." in id else parent,
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
                elif mname in self.ignoredMember:
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
                            is_dataclass(obj)
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
                            and islocal(tid)
                        ):
                            # dataclass has auto-generated methods, and has same qualname (a bug in cpython https://bugs.python.org/issue41747)
                            entry = self.visitFunc(
                                member, f"{id}.{mname}", parent=res.id
                            )
                        else:
                            entry = self.visitFunc(member, parent=res.id)
                    if len(entry.parameters) > 0:
                        if entry.parameters[0].name == "self":
                            entry.scope = ItemScope.Instance
                        elif inspect.ismethod(member):
                            entry.scope = ItemScope.Class
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
            except Exception as ex:
                self.logger.error(
                    f"Failed to extract class member {id}.{mname}: {member}",
                    exc_info=ex,
                )
            if isinstance(entry, ApiEntry):
                res.members[mname] = entry.id
            elif isinstance(entry, str):
                res.members[mname] = entry

        return res

    def visitFunc(
        self,
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

        res = FunctionEntry(id=id, parent=id.rsplit(".", 1)[0] if "." in id else parent)
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

                if para.annotation != inspect.Parameter.empty:
                    paraEntry.annotation = str(para.annotation)
                paraEntry.kind = self.PARA_KIND_MAP[para.kind]
                res.parameters.append(paraEntry)
        except Exception as ex:
            self.logger.error(
                f"Failed to extract function signature {id}.", exc_info=ex
            )

        return res

    def visitAttribute(
        self,
        attribute,
        id: "str",
        annotation: "str" = "",
        location: "Location | None" = None,
        parent: "str" = "",
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
