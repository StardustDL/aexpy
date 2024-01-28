from contextlib import contextmanager
from dataclasses import dataclass
import logging
from abc import ABC
from logging import Logger
from datetime import timedelta, datetime
import io

from .models import ProduceState, Product
from .utils import elapsedTimer, logWithStream


@dataclass
class ProducerOptions:
    def load(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


class Producer(ABC):
    """Producer that produces a product."""

    @classmethod
    def cls(cls):
        """Returns the class name of the producer, used by ProducerConfig."""
        return f"{cls.__module__}.{cls.__qualname__}"

    @property
    def name(self):
        return self._name if hasattr(self, "_name") else self.cls()

    @name.setter
    def name(self, value: str):
        self._name = value

    def __init__(self, logger: Logger | None = None):
        self.logger = (
            logger.getChild(self.name) if logger else logging.getLogger(self.name)
        )
        """The logger for the producer."""
        self.options = ProducerOptions()
        self.name = "aexpy"


class ProduceContext[T: Product]:
    def __init__(self, product: T, logger: Logger):
        self.logger = logger
        self.product = product
        self.producer: Producer | None = None
        self.exception: Exception | None = None
        self.log: str = ""

    def use(self, producer: Producer | None = None):
        self.producer = producer


@contextmanager
def produce[T: Product](product: T, logger: Logger | None = None):
    """
    Provide a context to produce product.
    """

    logger = logger or logging.getLogger()
    with elapsedTimer() as elapsed:
        with io.StringIO() as logStream:
            context = ProduceContext(product, logger)
            with logWithStream(logger, logStream):
                logger.info("Start producing.")
                try:
                    yield context
                    product.state = ProduceState.Success
                    logger.info("Finish producing.")
                except Exception as ex:
                    logger.error(
                        "Failed to produce.",
                        exc_info=ex,
                    )
                    product.state = ProduceState.Failure
                    context.exception = ex
            context.log = logStream.getvalue()

        product.creation = datetime.now()
        product.duration = elapsed()
        if context.producer is not None:
            product.producer = context.producer.name
