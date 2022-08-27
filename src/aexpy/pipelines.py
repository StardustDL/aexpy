import dataclasses
import logging
from logging import Logger

from aexpy.batching import Batcher
from aexpy.services import ProduceMode

from .diffing import Differ
from .extracting import Extractor
from .models import (ApiDescription, ApiDifference, BatchRequest, BatchResult, Distribution,
                     Release, ReleasePair, Report)
from .preprocessing import Preprocessor
from .reporting import Reporter


class Pipeline:
    """Pipeline."""

    def __init__(self, preprocessor: "Preprocessor", extractor: "Extractor", differ: "Differ", reporter: "Reporter", batcher: "Batcher", name: "str" = "default", logger: "Logger | None" = None) -> None:
        self.name = name
        self.preprocessor = preprocessor
        self.extractor = extractor
        self.differ = differ
        self.reporter = reporter
        self.batcher = batcher

        self.logger = logger or logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}")

        assert isinstance(self.preprocessor, Preprocessor)
        assert isinstance(self.extractor, Extractor)
        assert isinstance(self.differ, Differ)
        assert isinstance(self.reporter, Reporter)
        assert isinstance(self.batcher, Batcher)

    def preprocess(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "Distribution":
        """Preprocess release."""

        from .env import env
        services = env.services

        if mode != ProduceMode.Write:
            try:
                return services.preprocess(self.preprocessor.name, release, ProduceMode.Read)
            except Exception as ex:
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)
                if mode == ProduceMode.Read:
                    raise

        self.logger.info(f"Preprocess {release}.")
        return services.preprocess(self.preprocessor.name, release, mode)

    def extract(self, release: "Release", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDescription":
        """Extract release."""

        from .env import env
        services = env.services

        if mode != ProduceMode.Write:
            try:
                return services.extract(self.extractor.name, Distribution(release=release), ProduceMode.Read)
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
        return services.extract(self.extractor.name, dist, mode)

    def diff(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "ApiDifference":
        """Diff old and new release."""

        from .env import env
        services = env.services

        if mode != ProduceMode.Write:
            try:
                return services.diff(self.differ.name, ApiDescription(distribution=Distribution(release=pair.old)), ApiDescription(distribution=Distribution(release=pair.new)), ProduceMode.Read)
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
        return services.diff(self.differ.name, oldDes, newDes, mode)

    def report(self, pair: "ReleasePair", mode: "ProduceMode" = ProduceMode.Access) -> "Report":
        """Report breaking changes between old and new release."""

        from .env import env
        services = env.services

        if mode != ProduceMode.Write:
            try:
                distOld = Distribution(release=pair.old)
                distNew = Distribution(release=pair.new)
                return services.report(self.reporter.name,
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
        return services.report(self.reporter.name, pair.old, pair.new, oldDist, newDist, oldDesc, newDesc, diff, mode)

    def batch(self, request: "BatchRequest", mode: "ProduceMode" = ProduceMode.Access) -> "BatchResult":
        """Batch process releases."""

        from .env import env
        services = env.services

        request = dataclasses.replace(request, pipeline=self.name)

        if mode != ProduceMode.Write:
            try:
                return services.batch(self.batcher.name, request, ProduceMode.Read)
            except Exception as ex:
                if mode == ProduceMode.Read:
                    raise
                self.logger.warning(
                    f"Failed to load from cache.", exc_info=ex)

        self.logger.info(f"Batch process {request.project} releases.")
        return services.batch(self.batcher.name, request, mode)
