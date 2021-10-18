from ..analyses.models import ApiCollection
from .. import fsutils
from .differ import Differ
from . import serializer
from ..env import env


def diff(old: ApiCollection, new: ApiCollection):
    name = f"{old.manifest.project}@{old.manifest.version}-{new.manifest.project}@{new.manifest.version}"
    cache = env.cache.joinpath("diff")
    fsutils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{name}.json")
    if not cacheFile.exists() or env.redo:
        result = Differ().with_default_rules().process(old, new)
        cacheFile.write_text(serializer.serialize(result))
        return result

    return serializer.deserialize(cacheFile.read_text())
