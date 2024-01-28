from logging import Logger
from pathlib import Path
from uuid import uuid1
from typing import override

from aexpy.models.description import ApiEntry, ClassEntry, CollectionEntry, ModuleEntry
from aexpy.models.difference import DiffEntry
from aexpy.producers import ProducerOptions

from aexpy.models import ApiDescription, ApiDifference, Distribution
from . import Differ


class DefaultDiffer(Differ):
    @override
    def diff(self, old, new, product):
        from .differs.default import DefaultDiffer

        DefaultDiffer(self.logger).diff(old, new, product)

        from .evaluators.default import DefaultEvaluator

        DefaultEvaluator(self.logger).diff(old, new, product)
