
from .conda import CondaEnvironment


class DefaultEnvironment(CondaEnvironment):
    __baseenvprefix__ = "aexpy-extbase-"
    __envprefix__ = "aexpy-ext-"
    __packages__ = ["mypy"]
