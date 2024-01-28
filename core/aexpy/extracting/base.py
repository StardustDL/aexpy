import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, override
import json

from pydantic import TypeAdapter

from aexpy.models.description import TRANSFER_BEGIN, ApiEntryType, CollectionEntry, isPrivate

from .. import getAppDirectory
from ..models import ApiDescription, Distribution
from .environment import EnvirontmentExtractor


def resolveAlias(api: ApiDescription):
    alias: dict[str, set[str]] = {}
    working: set[str] = set()

    def resolve(entry: ApiEntryType):
        if entry.id in alias:
            return alias[entry.id]
        ret: set[str] = set()
        ret.add(entry.id)
        working.add(entry.id)
        for item in api.entries.values():
            if not isinstance(item, CollectionEntry):
                continue
            itemalias = None
            # ignore submodules and subclasses
            if item.id.startswith(f"{entry.id}."):
                continue
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


class BaseExtractor(EnvirontmentExtractor):
    """Basic extractor that uses dynamic inspect."""

    @override
    def extractInEnv(self, result, run, runPython):
        assert result.distribution

        subres = runPython(
            f"-m aexpy.extracting.main",
            cwd=getAppDirectory().parent,
            text=True,
            capture_output=True,
            input=result.distribution.model_dump_json(),
        )

        self.logger.info(f"Inner extractor exit with {subres.returncode}.")

        if subres.stdout.strip():
            self.logger.debug(f"STDOUT:\n{subres.stdout}")
        if subres.stderr.strip():
            self.logger.info(f"STDERR:\n{subres.stderr}")

        subres.check_returncode()

        data = subres.stdout.split(TRANSFER_BEGIN, 1)[1]
        entries: list[ApiEntryType] = TypeAdapter(list[ApiEntryType]).validate_json(data)
        for entry in entries:
            if entry.id not in result.entries:
                result.addEntry(entry)

        resolveAlias(result)
        for item in result.entries.values():
            if isPrivate(item):
                item.private = True
