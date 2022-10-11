from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .services import ServiceProvider


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

    @property
    def services(self) -> "ServiceProvider":
        assert self._services is not None, "No services set."
        return self._services

    @services.setter
    def services(self, value: "ServiceProvider"):
        self._services = value

    def __init__(self, logger: "Logger | None" = None) -> None:
        self.logger = logger.getChild(
            self.name) if logger else logging.getLogger(self.name)
        """The logger for the producer."""
        self.options = ProducerOptions()
        self.name = "empty"
        self._services: "ServiceProvider | None" = None
