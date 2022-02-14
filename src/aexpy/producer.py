from abc import ABC
from logging import Logger
import logging


class Producer(ABC):
    def __init__(self, logger: "Logger | None" = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__qualname__)
