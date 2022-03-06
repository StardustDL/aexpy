import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from aexpy.models.description import TRANSFER_BEGIN, ApiEntry, CollectionEntry

from .. import getAppDirectory
from ..models import ApiDescription, Distribution
from ..utils import elapsedTimer, ensureDirectory, logWithFile
from .environments import EnvirontmentExtractor


def resolveAlias(api: "ApiDescription"):
    alias: "dict[str, set[str]]" = {}
    working: "set[str]" = set()

    def resolve(entry: "ApiEntry"):
        if entry.id in alias:
            return alias[entry.id]
        ret: "set[str]" = set()
        ret.add(entry.id)
        working.add(entry.id)
        for item in api.entries.values():
            if not isinstance(item, CollectionEntry):
                continue
            itemalias = None
            for name, target in item.members.items():
                if target == entry.id:
                    if itemalias is None:
                        if item.id in working:  # cycle reference
                            itemalias = {item.id}
                        else:
                            itemalias = resolve(item)
                    for aliasname in itemalias:
                        ret.add(f"{aliasname}.{name}")
        alias[entry.id] = ret
        working.remove(entry.id)
        return ret

    for entry in api.entries.values():
        entry.alias = list(resolve(entry) - {entry.id})


class Extractor(EnvirontmentExtractor):
    """Basic extractor that uses dynamic inspect."""

    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "basic"

    def extractInEnv(self, result: "ApiDescription", run: "Callable[..., subprocess.CompletedProcess[str]]"):
        subres = run(f"python -m aexpy.extracting.main.basic", cwd=getAppDirectory().parent,
                     text=True, capture_output=True, input=result.distribution.dumps())

        self.logger.info(f"Inner extractor exit with {subres.returncode}.")

        if subres.stdout.strip():
            self.logger.debug(f"STDOUT:\n{subres.stdout}")
        if subres.stderr.strip():
            self.logger.info(f"STDERR:\n{subres.stderr}")

        subres.check_returncode()

        data = subres.stdout.split(TRANSFER_BEGIN, 1)[1]
        data = json.loads(data)
        result.load(data)
        resolveAlias(result)

    