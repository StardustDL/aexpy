import subprocess
import sys
import logging


class ExecutionEnvironment:
    """Environment that runs extractor code."""

    def __init__(
        self, logger: logging.Logger | None = None
    ) -> None:
        self.logger = logger or logging.getLogger("exe-env")
        """Python version of the environment."""

    def run(self, command: str, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the environment."""

        return subprocess.run(command, **kwargs)

    def runPython(self, command: str, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the environment."""

        return subprocess.run(f"python {command}", **kwargs)

    def __enter__(self):
        return self.run, self.runPython

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class CurrentEnvironment(ExecutionEnvironment):
    """Use the same environment for extractor."""

    def run(self, command: str, **kwargs):
        """Run a command in the environment."""

        return subprocess.run(command, **kwargs, shell=True)

    def runPython(self, command: str, **kwargs):
        """Run a command in the environment."""

        return self.run(f"{sys.executable} {command}", **kwargs)
