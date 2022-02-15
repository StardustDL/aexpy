from datetime import datetime, timedelta
import json
from typing import Callable

from ..utils import elapsedTimer, ensureDirectory, logWithFile
from ..models import Distribution, ApiDescription
from .environments import EnvirontmentExtractor
import subprocess
from .. import getAppDirectory


class Extractor(EnvirontmentExtractor):
    def extractInEnv(self, dist: "Distribution", run: "Callable[..., subprocess.CompletedProcess[str]]") -> "ApiDescription":
        logFile = self.cache / dist.release.project / \
            f"{dist.release.version}.log"
        ensureDirectory(logFile.parent)
        with logWithFile(self.logger, logFile):
            with elapsedTimer() as elapsed:
                result = run(f"python -m aexpy.extracting.main.basic", cwd=getAppDirectory().parent,
                             text=True, capture_output=True, input=dist.dumps())

            if result.stdout.strip():
                self.logger.info(f"STDOUT:\n{result.stdout}")
            if result.stderr.strip():
                self.logger.warning(f"STDERR:\n{result.stderr}")

            ret = ApiDescription()
            try:
                result.check_returncode()
                data = json.loads(result.stdout)
                ret.load(data)
            except Exception as ex:
                self.logger.error(
                    "Failed to load json from stdout", exc_info=ex)
                ret.success = False
            ret.duration = timedelta(seconds=elapsed())
            ret.distribution = dist
            ret.creation = datetime.now()
            ret.logFile = logFile

            return ret

    def extract(self, dist: "Distribution") -> "ApiDescription":
        cacheDir = self.cache / dist.release.project
        ensureDirectory(cacheDir)
        cacheFile = cacheDir / f"{dist.release.version}.json"
        if not cacheFile.exists() or self.redo:
            result = super().extract(dist)
            cacheFile.write_text(result.dumps())
        else:
            result = ApiDescription()
            result.load(json.loads(cacheFile.read_text()))
        return result
