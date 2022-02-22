import code
import json
import pathlib
import subprocess
from datetime import datetime, timedelta
from logging import Logger
from pathlib import Path
from typing import Callable
from uuid import uuid1

from aexpy import getCacheDirectory
from aexpy.differing import Differ
from aexpy.env import PipelineConfig, ProducerConfig
from aexpy.evaluating import Evaluator
from aexpy.extracting import Extractor
from aexpy.models import (ApiBreaking, ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline as Base
from aexpy.preprocessing import Preprocessor
from aexpy.reporting import Reporter
from aexpy.reporting.generators import GeneratorReporter


def getDefault() -> "PipelineConfig":
    from aexpy.preprocessing.default import Preprocessor as PPreprocessor

    from .differ import Differ as PDiffer
    from .evaluator import Evaluator as PEvaluator
    from .extractor import Extractor as PExtractor
    from .reporter import Reporter as PReporter

    return PipelineConfig(
        name="pycompat",
        preprocess=ProducerConfig.fromProducer(PPreprocessor),
        extractor=ProducerConfig.fromProducer(PExtractor),
        differ=ProducerConfig.fromProducer(PDiffer),
        evaluator=ProducerConfig.fromProducer(PEvaluator),
        reporter=ProducerConfig.fromProducer(PReporter),
    )
