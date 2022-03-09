import subprocess
from abc import abstractmethod
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import json
from aexpy.models import ApiDescription, Distribution
from aexpy.producer import ProducerOptions


class ExecutionEnvironment:
    """Environment that runs extractor code."""

    def __init__(self, pythonVersion: str = "3.7") -> None:
        self.pythonVersion = pythonVersion
        """Python version of the environment."""

    def run(self, command: str, **kwargs):
        """Run a command in the environment."""

        return subprocess.run(command, **kwargs)

    def __enter__(self):
        return self.run

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
