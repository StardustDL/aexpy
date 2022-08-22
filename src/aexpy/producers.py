from dataclasses import dataclass
from enum import IntEnum
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path

from aexpy import utils
from aexpy.models import ProduceCache, ProduceState, Product
from aexpy import json


@dataclass
class ProducerOptions:    
    def load(self, data: "dict"):
        for k, v in data.items():
            setattr(self, k, v)


class Producer(ABC):
    """Producer that produces a product."""

    @classmethod
    def cls(cls) -> "str":
        """Returns the class name of the producer, used by ProducerConfig."""
        return f"{cls.__module__}.{cls.__qualname__}"

    @property
    def name(self) -> "str":
        return self._name if hasattr(self, "_name") else self.cls()

    @name.setter
    def name(self, value: "str") -> None:
        self._name = value

    def __init__(self, logger: "Logger | None" = None) -> None:
        self.logger = logger.getChild(
            self.name()) if logger else logging.getLogger(self.name())
        """The logger for the producer."""
        self.options = ProducerOptions(name=self.cls())
