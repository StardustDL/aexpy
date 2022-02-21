from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Callable

from aexpy.models.description import TRANSFER_BEGIN

from ..utils import elapsedTimer, ensureDirectory, logWithFile
from ..models import Distribution, ApiDescription
from .environments import EnvirontmentExtractor
import subprocess
from .. import getAppDirectory


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
