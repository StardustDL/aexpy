import inspect


def isFunction(obj) -> "bool":
    return inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj) or inspect.isgeneratorfunction(obj)


def getModuleName(obj) -> "str | None":
    module = inspect.getmodule(obj)
    if module:
        return module.__name__
    else:
        return getattr(obj, "__module__", None)


def getObjectId(obj) -> "str":
    if inspect.ismodule(obj):
        return obj.__name__

    moduleName = getModuleName(obj)
    if moduleName:
        return f"{moduleName}.{obj.__qualname__}"
    else:
        return obj.__qualname__
