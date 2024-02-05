import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, override
import json
import tempfile

from pydantic import TypeAdapter

from aexpy.models.description import (
    TRANSFER_BEGIN,
    ApiEntryType,
    CollectionEntry,
    isPrivate,
)
from aexpy.utils import logProcessResult

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
    def extractInEnv(self, result, runner):
        assert result.distribution

        with tempfile.TemporaryDirectory() as tmpdir:
            
            # pydantic will failed if run in app directory under python 3.12 in another python
            self.logger.info(f"Copy from {getAppDirectory()} to {tmpdir}")
            shutil.copytree(getAppDirectory(), Path(tmpdir) / "aexpy")

            subres = runner.runPythonText(
                f"-m aexpy.apidetector",
                cwd=tmpdir,
                input=result.distribution.model_dump_json(),
            )

        logProcessResult(self.logger, subres)

        subres.check_returncode()

        data = subres.stdout.split(TRANSFER_BEGIN, 1)[1]
        entries: list[ApiEntryType] = TypeAdapter(list[ApiEntryType]).validate_json(
            data
        )
        for entry in entries:
            if entry.id not in result.entries:
                result.addEntry(entry)

        resolveAlias(result)
        for item in result.entries.values():
            if isPrivate(item):
                item.private = True
