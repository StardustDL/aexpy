import io
import logging
from abc import ABC
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from logging import Logger

from .models import ProduceState, Product
from .utils import elapsedTimer, getObjectId, logWithStream


@dataclass
class ProducerOptions:
    def load(self, /, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


class Producer(ABC):
    """Producer that produces a product."""

    @classmethod
    def cls(cls, /):
        return cls.__qualname__

    @property
    def name(self, /):
        return self._name if hasattr(self, "_name") else self.cls()

    @name.setter
    def name(self, /, value: str):
        self._name = value

    def __init__(self, /, logger: Logger | None = None):
        self.logger = (
            logger.getChild(self.name) if logger else logging.getLogger(self.name)
        )
        """The logger for the producer."""
        self.options = ProducerOptions()


class ProduceContext[T: Product]:
    def __init__(self, /, product: T, logger: Logger):
        self.logger = logger
        self.product = product
        self.exception: Exception | None = None
        self.log: str = ""
        self.producers: list[str] = []

    def combinedProducers(self, /, rootProducer: Producer | str = ""):
        if isinstance(rootProducer, Producer):
            prefix = rootProducer.cls()
        else:
            prefix = rootProducer

        return f"{prefix}[{','.join(self.producers)}]"

    @contextmanager
    def using[P: Producer](self, /, producer: P):
        originalLogger = producer.logger
        producer.logger = self.logger

        name = f"{getObjectId(producer.__class__)}: {producer.name}"
        self.logger.debug(f"Using producer {name}")
        with elapsedTimer() as timer:
            try:
                yield producer
            except Exception:
                self.logger.error(
                    f"Error when using producer {name}",
                    exc_info=True,
                )
                raise
            finally:
                self.producers.append(producer.name)
                self.logger.info(f"Used producer {name} ({timer().total_seconds()}s)")
                producer.logger = originalLogger


@contextmanager
def produce[
    T: Product
](product: T, logger: Logger | None = None, service: str = "", raising: bool = False):
    """
    Provide a context to produce product.
    """

    logger = logger or logging.getLogger()
    with elapsedTimer() as elapsed:
        with io.StringIO() as logStream:
            context = ProduceContext(product, logger)
            with logWithStream(logger, logStream):
                logger.debug("Start producing.")
                try:
                    yield context
                    product.state = ProduceState.Success
                    logger.debug("Finish producing.")
                except Exception as ex:
                    logger.error(
                        "Failed to produce.",
                        exc_info=True,
                    )
                    product.state = ProduceState.Failure
                    context.exception = ex
            context.log = logStream.getvalue()

        product.creation = datetime.now()
        product.duration = elapsed()
        product.producer = context.combinedProducers(service)

    if context.exception and raising:
        raise Exception("Failed to produce") from context.exception
