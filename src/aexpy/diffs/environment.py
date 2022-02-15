import logging

from .. import utils
from ..analyses.models import ApiCollection
from ..env import env
from . import serializer
from .differ import Differ


def diff(old: ApiCollection, new: ApiCollection):
    logger = logging.getLogger("diff")

    name = f"{old.manifest.project}@{old.manifest.version}-{new.manifest.project}@{new.manifest.version}"
    cache = env.cache.joinpath("diff")
    utils.ensureDirectory(cache)
    cacheFile = cache.joinpath(f"{name}.json")
    if not cacheFile.exists() or env.redo:
        logger.info(f"Diff {name}")
        result = Differ().with_default_rules().process(old, new)
        cacheFile.write_text(serializer.serialize(result))
        return result

    return serializer.deserialize(cacheFile.read_text())
