import subprocess
import sys
import logging

from .. import getPythonExe


class ExecutionEnvironment:
    """Environment that runs extractor code."""

    def __init__(self, pythonVersion: str = "3.8", logger: logging.Logger | None = None) -> None:
        self.pythonVersion = pythonVersion
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

    def __init__(self, pythonVersion: str = "3.8", logger: logging.Logger | None = None) -> None:
        currentVersion = sys.version.split(maxsplit=1)[0]
        super().__init__(currentVersion, logger)
        if pythonVersion != currentVersion:
            self.logger.warning(f"Current environment only support {currentVersion}, not {pythonVersion}.")

    def run(self, command: str, **kwargs):
        """Run a command in the environment."""

        return subprocess.run(command, **kwargs, shell=True)
    
    def runPython(self, command: str, **kwargs):
        """Run a command in the environment."""

        return self.run(f"{getPythonExe()} {command}", **kwargs)
