from datetime import datetime
import importlib
import inspect
import logging
import pathlib
import platform
from types import ModuleType
import mypy
import sys
import json
from aexpy import initializeLogging
from aexpy.models import ApiDescription, Distribution, Release
from aexpy.models.description import Parameter, ParameterKind, ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry, SpecialEntry, SpecialKind, CollectionEntry, Location


# Builtin ABCs (https://docs.python.org/3/glossary.html#term-abstract-base-class)
from collections.abc import Container, Hashable, Iterable, Iterator, Reversible, Generator, Sized, Callable, Collection, Sequence, MutableSequence, ByteString, Set, MutableSet, Mapping, MutableMapping, MappingView, ItemsView, KeysView, ValuesView, Awaitable, Coroutine, AsyncIterable, AsyncIterator, AsyncGenerator
from numbers import Complex, Real, Rational, Integral
from io import IOBase, RawIOBase, BufferedIOBase, TextIOBase
from importlib.abc import Loader, Finder, MetaPathFinder, PathEntryFinder, ResourceLoader, InspectLoader, ExecutionLoader, FileLoader, SourceLoader
ABCs = [Container, Hashable, Iterable, Iterator, Reversible, Generator, Sized, Callable, Collection, Sequence, MutableSequence, ByteString, Set, MutableSet, Mapping, MutableMapping, MappingView, ItemsView, KeysView, ValuesView, Awaitable, Coroutine, AsyncIterable, AsyncIterator, AsyncGenerator,
        Complex, Real, Rational, Integral,
        IOBase, RawIOBase, BufferedIOBase, TextIOBase,
        Loader, Finder, MetaPathFinder, PathEntryFinder, ResourceLoader, InspectLoader, ExecutionLoader, FileLoader, SourceLoader]


class Processor:
    PARA_KIND_MAP = {
        inspect.Parameter.KEYWORD_ONLY: ParameterKind.Keyword,
        inspect.Parameter.VAR_KEYWORD: ParameterKind.VarKeyword,
        inspect.Parameter.VAR_POSITIONAL: ParameterKind.VarPositional,
        inspect.Parameter.POSITIONAL_ONLY: ParameterKind.Positional,
        inspect.Parameter.POSITIONAL_OR_KEYWORD: ParameterKind.PositionalOrKeyword,
    }

    ignoredClassMember = {"__weakref__", "__dict__", "__annotations__",
                          "__doc__", "__init_subclass__", "__module__", "__subclasshook__"}

    def __init__(self, result: "ApiDescription") -> None:
        self.result = result
        self.mapper: "dict[str, ApiEntry]" = {}
        self.logger = logging.getLogger("processor")
        if "$external$" not in result.entries:
            self.externalEntry = SpecialEntry(
                id="$external$", kind=SpecialKind.External)
            self.addEntry(self.externalEntry)
        else:
            self.externalEntry = result.entries["$external$"]

    def process(self, root: "ModuleType", modules: "list[ModuleType]"):
        self.root = root
        self.rootPath = pathlib.Path(root.__file__).parent.absolute()

        self.visitModule(self.root)

        for module in modules:
            if module == root:
                continue
            try:
                self.visitModule(module)
            except Exception as ex:
                self.logger.error(
                    f"Failed to visit module {module}.", exc_info=ex)

        for v in self.mapper.values():
            self.result.addEntry(v)

    def addEntry(self, entry: ApiEntry):
        if entry.id in self.mapper:
            raise Exception(f"Id {entry.id} has existed.")
        self.mapper[entry.id] = entry

    def _getModuleName(self, obj) -> "str | None":
        module = inspect.getmodule(obj)
        if module:
            return module.__name__
        else:
            return getattr(obj, "__module__", None)

    def _getId(self, obj) -> "str":
        if inspect.ismodule(obj):
            return obj.__name__

        moduleName = self._getModuleName(obj)
        if moduleName:
            return f"{moduleName}.{obj.__qualname__}"
        else:
            return obj.__qualname__

    def _visitEntry(self, result: "ApiEntry", obj) -> None:
        if "." in result.id:
            result.name = result.id.split('.')[-1]
        else:
            result.name = result.id

        if isinstance(result, AttributeEntry):
            return

        if isinstance(result, CollectionEntry) or isinstance(result, FunctionEntry):
            # result.annotations = { k: str(v) for k, v in inspect.get_annotations(obj).items()}
            annotations = getattr(obj, "__annotations__", {})
            result.annotations = {k: str(v) for k, v in annotations.items()}

        location = Location()

        location.module = self._getModuleName(obj) or ""

        module = inspect.getmodule(obj)

        try:
            file = inspect.getfile(obj)
            if not file.startswith(str(self.rootPath)) and module:
                file = inspect.getfile(module)
            if file.startswith(str(self.rootPath)):
                location.file = str(pathlib.Path(
                    file).relative_to(self.rootPath.parent))
        except Exception as ex:
            self.logger.error(
                f"Failed to get location for {result.id}", exc_info=ex)

        try:
            sl = inspect.getsourcelines(obj)
            src = "".join(sl[0])
            result.src = src
            location.line = sl[1]
        except Exception as ex:
            self.logger.error(
                f"Failed to get source code for {result.id}", exc_info=ex)
        result.doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        result.comments = inspect.getcomments(obj) or ""
        result.location = location

    def _isExternal(self, obj) -> "bool":
        try:
            moduleName = self._getModuleName(obj)
            if moduleName:
                return not moduleName.startswith(self.root.__name__)
            if inspect.ismodule(obj) or inspect.isclass(obj) or inspect.isfunction(obj):
                try:
                    return not inspect.getfile(obj).startswith(str(self.rootPath))
                except:
                    return True  # fail to get file -> a builtin module
        except:
            pass
        return False

    def _isFunction(self, obj) -> "bool":
        return inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj) or inspect.isgeneratorfunction(obj)

    def visitModule(self, obj) -> "ModuleEntry":
        assert inspect.ismodule(obj)

        id = self._getId(obj)

        if id in self.mapper:
            assert isinstance(self.mapper[id], ModuleEntry)
            return self.mapper[id]

        self.logger.debug(f"Module: {id}")

        res = ModuleEntry(id=id)
        self._visitEntry(res, obj)
        self.addEntry(res)

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                if self._isExternal(member):
                    entry = self.externalEntry
                elif inspect.ismodule(member):
                    entry = self.visitModule(member)
                elif inspect.isclass(member):
                    entry = self.visitClass(member)
                elif self._isFunction(member):
                    entry = self.visitFunc(member)
                else:
                    entry = self.visitAttribute(
                        member, f"{id}.{mname}", res.location)
            except Exception as ex:
                self.logger.error(
                    f"Failed to extract module member {id}.{mname}: {member}", exc_info=ex)
            if entry:
                res.members[mname] = entry.id
        return res

    def visitClass(self, obj) -> "ClassEntry":
        assert inspect.isclass(obj)

        id = self._getId(obj)

        if id in self.mapper:
            assert isinstance(self.mapper[id], ClassEntry)
            return self.mapper[id]

        self.logger.debug(f"Class: {id}")

        bases = obj.__bases__

        abcs = []

        for abc in ABCs:
            if issubclass(obj, abc):
                abcs.append(self._getId(abc))

        res = ClassEntry(id=id,
                         bases=[self._getId(b) for b in obj.__bases__],
                         abcs=abcs,
                         mro=[self._getId(b) for b in inspect.getmro(obj)],
                         slots=[str(s) for s in getattr(obj, "__slots__", [])])
        self._visitEntry(res, obj)
        self.addEntry(res)

        slots = set(res.slots)

        for mname, member in inspect.getmembers(obj):
            entry = None
            try:
                if any((base for base in bases if member is getattr(base, mname, None))):  # ignore parent
                    pass
                elif mname in self.ignoredClassMember:
                    pass
                elif self._isExternal(member):
                    entry = self.externalEntry
                elif inspect.ismodule(member):
                    entry = self.visitModule(member)
                elif inspect.isclass(member):
                    entry = self.visitClass(member)
                elif self._isFunction(member):
                    entry = self.visitFunc(member)
                else:
                    entry = self.visitAttribute(
                        member, f"{id}.{mname}", res.location)
                    if mname in slots:
                        entry.bound = True
            except Exception as ex:
                self.logger.error(
                    f"Failed to extract class member {id}.{mname}: {member}", exc_info=ex)
            if entry:
                res.members[mname] = entry.id

        return res

    def visitFunc(self, obj) -> "FunctionEntry":
        assert self._isFunction(obj)

        id = self._getId(obj)

        if id in self.mapper:
            assert isinstance(self.mapper[id], FunctionEntry)
            return self.mapper[id]

        self.logger.debug(f"Function: {id}")

        res = FunctionEntry(id=id)
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
                f"Failed to extract function signature {id}.", exc_info=ex)

        return res

    def visitAttribute(self, attribute, id: "str", location: "Location | None" = None) -> "AttributeEntry":
        if id in self.mapper:
            assert isinstance(self.mapper[id], AttributeEntry)
            return self.mapper[id]

        self.logger.debug(f"Attribute: {id}")

        res = AttributeEntry(id=id, rawType=str(type(attribute)))

        self._visitEntry(res, attribute)

        if location and not res.location:
            res.location = location
        self.addEntry(res)
        return res


def importModule(name: str) -> "list[ModuleType]":
    logger = logging.getLogger("import")
    logger.debug(f"Import {name}.")

    module = importlib.import_module(name)

    modules = [module]

    file = getattr(module, "__file__", None)

    if file:
        file = pathlib.Path(file)
        if file.name == "__init__.py":
            for submodulefile in file.parent.iterdir():
                submodule = None
                if submodulefile.is_dir():
                    if submodulefile.joinpath("__init__.py").exists():
                        submodule = pathlib.Path(submodulefile).stem
                else:
                    if submodulefile.stem != "__init__" and submodulefile.stem != "__main__" and submodulefile.suffix == ".py":
                        submodule = pathlib.Path(submodulefile).stem
                if submodule:
                    moduleName = ".".join([name, submodule])
                    try:
                        sub = importModule(moduleName)
                        modules.extend(sub)
                    except Exception as ex:
                        logger.error(
                            f"Failed to import {moduleName}", exc_info=ex)
                    except SystemExit as ex:
                        logger.error(
                            f"Failed to import {moduleName}", exc_info=ex)

    return modules


def main(dist: "Distribution"):
    logger = logging.getLogger("main")

    platformStr = f"{platform.platform()} {platform.machine()} {platform.processor()} {platform.python_implementation()} {platform.python_version()}"
    logging.info(f"Platform: {platformStr}")

    result = ApiDescription()

    processor = Processor(result)

    for topLevel in dist.topModules:
        modules = None

        try:
            logger.info(f"Import module {topLevel}.")

            modules = importModule(topLevel)
        except Exception as ex:
            logger.error(f"Failed to import module {topLevel}.", exc_info=ex)
            modules = None

        if modules:
            try:
                logger.info(f"Extract {topLevel} ({modules}).")

                processor.process(modules[0], modules)
            except Exception as ex:
                logger.error(
                    f"Failed to extract {topLevel}: {modules}.", exc_info=ex)

    return result


if __name__ == '__main__':
    initializeLogging(logging.NOTSET)
    dist = Distribution()
    dist.load(json.loads(sys.stdin.read()))
    print(main(dist).dumps())
