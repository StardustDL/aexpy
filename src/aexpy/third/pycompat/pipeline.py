import code
from logging import Logger
import pathlib
from aexpy import getCacheDirectory
from aexpy.differing import Differ
from aexpy.evaluating import Evaluator
from aexpy.extracting import Extractor
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.reporting import Reporter as Base
from logging import Logger
from pathlib import Path
import subprocess
from uuid import uuid1
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.preprocessing import Preprocessor
from aexpy.models import ApiBreaking, ApiDifference, Release, ApiDescription
from aexpy.pipelines import Pipeline as Base

from datetime import datetime, timedelta
import json
from typing import Callable
import subprocess

from aexpy.reporting.generators import GeneratorReporter


class Pipeline(Base):
    def __init__(self, preprocessor: "Preprocessor | None" = None, extractor: "Extractor | None" = None, differ: "Differ | None" = None, evaluator: "Evaluator | None" = None, reporter: "Base | None" = None, redo: "bool | None" = None, cached: "bool | None" = None) -> None:
        from .differ import Differ as PDiffer
        from .evaluator import Evaluator as PEvaluator
        from .extractor import Extractor as PExtractor
        extractor = extractor or PExtractor()
        evaluator = evaluator or PEvaluator()
        differ = differ or PDiffer()
        reporter = GeneratorReporter(
            cache=getCacheDirectory() / "pycompat" / "reporting")
        super().__init__(preprocessor, extractor, differ, evaluator, reporter, redo, cached)
