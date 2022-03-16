from typing import Any
import inspect


def log(obj: "Any"):
    print(f"Object: {obj}")


def bindParameters(func, *args, **kwargs):
    inspect.signature(func).bind(*args, **kwargs)