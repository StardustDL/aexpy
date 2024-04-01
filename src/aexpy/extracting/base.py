import shutil
import tempfile
from pathlib import Path
from typing import Annotated, override

from pydantic import Field, TypeAdapter

from .. import getAppDirectory
from ..models import ApiDescription, Distribution
from ..models.description import (TRANSFER_BEGIN, ApiEntryType,
                                  CollectionEntry, isPrivate)
from ..utils import logProcessResult
from .environment import EnvirontmentExtractor


class BaseExtractor(EnvirontmentExtractor):
    """Basic extractor that uses dynamic inspect."""

    @override
    def extractInEnv(self, /, result, runner):
        assert result.distribution

        with tempfile.TemporaryDirectory() as tmpdir:

            # pydantic will failed if run in app directory under python 3.12 in another python
            self.logger.debug(f"Copy from {getAppDirectory()} to {tmpdir}")
            shutil.copytree(
                getAppDirectory() / "apidetector", Path(tmpdir) / "aexpy_apidetector"
            )

            subres = runner.runPythonText(
                f"-m aexpy_apidetector",
                cwd=tmpdir,
                input=result.distribution.model_dump_json(),
            )

        logProcessResult(self.logger, subres)

        subres.check_returncode()

        data = subres.stdout.split(TRANSFER_BEGIN, 1)[1]
        entries: list[ApiEntryType] = TypeAdapter(
            list[Annotated[ApiEntryType, Field(discriminator="form")]]
        ).validate_json(data)
        for entry in entries:
            if entry.id not in result:
                result.add(entry)

        result.calcAliases()
        for item in result:
            if isPrivate(item):
                item.private = True
        for mod in result.modules.values():
            if mod.slots is None:
                continue
            for member, target in mod.members.items():
                entry = result[target]
                if entry is not None and entry.parent == mod.id and len(entry.alias) == 0:
                    entry.private = member not in mod.slots

        result.calcSubclasses()
