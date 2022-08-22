from typing import Any
import inspect


def log(obj: "Any"):
    print(f"Object: {obj}")


def bindParameters(func, *args, **kwargs):
    ret = inspect.signature(func).bind(*args, **kwargs)
    ret.apply_defaults()
    log(ret)
    return ret

def assertArgument(args, name, value):
    assert name in args.arguments
    val = args.arguments[name]
    assert val == value, f"{name}: {val} != {value}"


def assertArgumentDefault(args, name, value):
    assert name in args.arguments
    val = args.arguments[name]
    if value is None:
        assert val == value, f"{name}: {val} != {value}"
    else:
        des = f"{type(val).__name__}('{str(val)}')"
        assert des == value, f"{name}: {des} != {value}"
