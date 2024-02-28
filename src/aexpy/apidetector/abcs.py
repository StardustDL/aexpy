# Builtin ABCs (https://docs.python.org/3/glossary.html#term-abstract-base-class)
import importlib
import logging

BuiltinABCPaths = {
    "collections.abc": [
        "AsyncGenerator",
        "AsyncIterable",
        "AsyncIterator",
        "Awaitable",
        "ByteString",
        "Callable",
        "Collection",
        "Container",
        "Coroutine",
        "Generator",
        "Hashable",
        "ItemsView",
        "Iterable",
        "Iterator",
        "KeysView",
        "Mapping",
        "MappingView",
        "MutableMapping",
        "MutableSequence",
        "MutableSet",
        "Reversible",
        "Sequence",
        "Set",
        "Sized",
        "ValuesView",
        "Buffer",
    ],
    "importlib.abc": [
        "ExecutionLoader",
        "Finder",
        "FileLoader",
        "InspectLoader",
        "Loader",
        "MetaPathFinder",
        "PathEntryFinder",
        "ResourceLoader",
        "SourceLoader",
    ],
    "importlib.resources": ["TraversableResources"],
    "io": [
        "BufferedIOBase",
        "IOBase",
        "RawIOBase",
        "TextIOBase",
    ],
    "numbers": [
        "Complex",
        "Integral",
        "Rational",
        "Real",
        "Number",
    ],
    "typing": [
        "SupportsAbs",
        "SupportsBytes",
        "SupportsComplex",
        "SupportsFloat",
        "SupportsIndex",
        "SupportsInt",
        "SupportsRound",
        "IO",
        "TextIO",
        "BinaryIO",
    ],
}


def buildBuiltinABCs(logger: logging.Logger):
    result = []
    for moduleName, classes in BuiltinABCPaths.items():
        try:
            module = importlib.import_module(moduleName)
            for clsName in classes:
                try:
                    cls = getattr(module, clsName)
                    result.append(cls)
                except Exception:
                    logger.error(
                        f"Failed to get class {clsName} from {moduleName} for ABCs",
                        exc_info=True,
                    )
        except Exception:
            logger.error(f"Failed to import {moduleName} for ABCs", exc_info=True)
    return result
