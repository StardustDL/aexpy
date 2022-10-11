from dataclasses import dataclass
import dataclasses
import logging
from logging import Logger
from typing import TYPE_CHECKING

from aexpy.batching import Batcher
from aexpy.models import ProduceMode

from .diffing import Differ
from .extracting import Extractor
from .models import (ApiDescription, ApiDifference, BatchRequest, BatchResult, Distribution,
                     Release, ReleasePair, Report)
from .preprocessing import Preprocessor
from .reporting import Reporter

if TYPE_CHECKING:
    from .services import ServiceProvider


@dataclass
class PipelineConfig:
    """Configuration for Pipeline."""

    name: "str" = "default"
    """The name of the pipeline."""

    preprocessor: "str" = ""
    """The preprocess producer name."""

    extractor: "str" = ""
    """The extractor producer name."""

    differ: "str" = ""
    """The differ producer name."""

    reporter: "str" = ""
    """The reporter producer name."""

    batcher: "str" = ""
    """The batcher producer name."""

    @classmethod
    def load(cls, data: "dict") -> "PipelineConfig":
        """Loads the configuration from a dictionary."""
        return cls(**data)


class Pipeline:
    """Processing pipeline on a service provider."""

    def __init__(self, services: "ServiceProvider", config: "PipelineConfig", logger: "Logger | None" = None) -> None:
        self.services = services
        self.config = config
        self.name = config.name
        self.preprocessor = config.preprocessor
        self.extractor = config.extractor
        self.differ = config.differ
        self.reporter = config.reporter
        self.batcher = config.batcher

        self.logger = logger or logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}")

        assert isinstance(services.getProducer(
            self.preprocessor), Preprocessor)
        assert isinstance(services.getProducer(self.extractor), Extractor)
        assert isinstance(services.getProducer(self.differ), Differ)
        assert isinstance(services.getProducer(self.reporter), Reporter)
        assert isinstance(services.getProducer(self.batcher), Batcher)

    def preprocess(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "Distribution":
        """Preprocess release."""

        services = self.services

        if mode != ProduceMode.Write:
            try:
                return services.preprocess(self.preprocessor, release, ProduceMode.Read)
            except Exception as ex:
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)
                if mode == ProduceMode.Read:
                    raise

        self.logger.info(f"Preprocess {release}.")
        return services.preprocess(self.preprocessor, release, mode)

    def extract(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDescription":
        """Extract release."""

        services = self.services

        if mode != ProduceMode.Write:
            try:
                return services.extract(self.extractor, Distribution(release=release), ProduceMode.Read)
            except Exception as ex:
                if mode == ProduceMode.Read:
                    raise
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        try:
            dist = self.preprocess(release)
            assert dist.success, f"Failed to preprocess {release}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                dist = self.preprocess(release, ProduceMode.Write)
                if not dist.success:
                    raise

        self.logger.info(f"Extract {release}.")
        return services.extract(self.extractor, dist, mode)

    def diff(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDifference":
        """Diff old and new release."""

        services = self.services

        if mode != ProduceMode.Write:
            try:
                return services.diff(self.differ, ApiDescription(distribution=Distribution(release=pair.old)), ApiDescription(distribution=Distribution(release=pair.new)), ProduceMode.Read)
            except Exception as ex:
                if mode == ProduceMode.Read:
                    raise
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        try:
            oldDes = self.extract(pair.old)
            assert oldDes.success, f"Failed to extract {pair.old}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                oldDes = self.extract(pair.old, ProduceMode.Write)
                if not oldDes.success:
                    raise

        try:
            newDes = self.extract(pair.new)
            assert newDes.success, f"Failed to extract {pair.new}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                newDes = self.extract(pair.new, ProduceMode.Write)
                if not newDes.success:
                    raise

        self.logger.info(f"Diff {pair.old} and {pair.new}.")
        return services.diff(self.differ, oldDes, newDes, mode)

    def report(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "Report":
        """Report breaking changes between old and new release."""

        services = self.services

        if mode != ProduceMode.Write:
            try:
                distOld = Distribution(release=pair.old)
                distNew = Distribution(release=pair.new)
                return services.report(self.reporter,
                                       pair.old, pair.new,
                                       distOld, distNew,
                                       ApiDescription(distribution=distOld),
                                       ApiDescription(distribution=distNew),
                                       ApiDifference(old=distOld, new=distNew),
                                       ProduceMode.Read)
            except Exception as ex:
                if mode == ProduceMode.Read:
                    raise
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        try:
            diff = self.diff(pair)
            assert diff.success, f"Failed to diff {pair.old} and {pair.new}"
        except:
            if mode == ProduceMode.Access:
                raise
            else:
                diff = self.diff(pair, ProduceMode.Write)
                if not diff.success:
                    raise

        oldDist = self.preprocess(pair.old)
        newDist = self.preprocess(pair.new)
        oldDesc = self.extract(pair.old)
        newDesc = self.extract(pair.new)
        diff = self.diff(pair)

        self.logger.info(f"Report {pair.old} and {pair.new}.")
        return services.report(self.reporter, pair.old, pair.new, oldDist, newDist, oldDesc, newDesc, diff, mode)

    def batch(self, request: "BatchRequest", mode: "ProduceMode" = ProduceMode.Access) -> "BatchResult":
        """Batch process releases."""

        services = self.services

        request = dataclasses.replace(request, pipeline=self.name)

        if mode != ProduceMode.Write:
            try:
                return services.batch(self.batcher, request, ProduceMode.Read)
            except Exception as ex:
                if mode == ProduceMode.Read:
                    raise
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        self.logger.info(f"Batch process {request.project} releases.")
        return services.batch(self.batcher, request, mode)
