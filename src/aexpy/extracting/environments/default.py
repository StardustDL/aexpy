
from aexpy.environments.conda import CondaEnvironment


class DefaultEnvironment(CondaEnvironment):
    """Environment for default extractor."""

    __baseenvprefix__ = "aexpy-extbase-"
    __envprefix__ = "aexpy-ext-"
