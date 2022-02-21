from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import subprocess
from aexpy import getCacheDirectory, getAppDirectory

from aexpy.models import Product
from aexpy.producer import DefaultProducer


@dataclass
class ProjectProcessingResult(Product):
    """
    A result of a batch run.
    """
    project: "str" = ""
    provider: "str" = ""

    def load(self, data: "dict"):
        super().load(data)
        if "project" in data and data["project"] is not None:
            self.release = data.pop("project")
        if "provider" in data and data["provider"] is not None:
            self.provider = data.pop("provider")


class DataProcessor(DefaultProducer):
    def getCommandPrefix(self) -> "list[str]":
        return ["python", "-u", "-m", "aexpy", "-c", str(getCacheDirectory())]

    def defaultCache(self) -> "Path | None":
        return getCacheDirectory() / "processing"

    def getProduct(self, project: "str", provider: "str") -> "ProjectProcessingResult":
        return ProjectProcessingResult(project=project, provider=provider)

    def getCacheFile(self, project: "str", provider: "str") -> "Path | None":
        return self.cache / provider / f"{project}.json"

    def process(self, product: "ProjectProcessingResult", project: "str", provider: "str"):
        self.logger.info(
            f"Processing {project} by {provider} @ {datetime.now()}")

        cmdpre = self.getCommandPrefix()

        subres = subprocess.run(
            [*cmdpre, "-p", provider, "pro", project], cwd=getAppDirectory().parent, capture_output=True, text=True)

        self.logger.info(
            f"Processed {project} by {provider} @ {datetime.now()}, exit with {subres.returncode}.")

        if subres.stdout.strip():
            self.logger.debug(f"STDOUT:\n{subres.stdout}")
        if subres.stderr.strip():
            self.logger.info(f"STDERR:\n{subres.stderr}")

        subres.check_returncode()

    def batch(self, project: "str", provider: "str"):
        return self.produce(project=project, provider=provider)


class DataDockerProcessor(DataProcessor):
    def getCommandPrefix(self) -> "list[str]":
        return ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", "-v", f"{str(getCacheDirectory())}:/data", "aexpy"]
