import code
from logging import Logger
import pathlib
from aexpy import getCacheDirectory
from aexpy.differing import Differ
from aexpy.env import PipelineConfig, ProducerConfig
from aexpy.evaluating import Evaluator
from aexpy.extracting import Extractor
from aexpy.models import ApiBreaking, ApiDescription, ApiDifference, Distribution, Report
from aexpy.reporting import Reporter
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


def getDefault() -> "PipelineConfig":
    from aexpy.preprocessing.default import Preprocessor as PPreprocessor
    from .differ import Differ as PDiffer
    from .evaluator import Evaluator as PEvaluator
    from .extractor import Extractor as PExtractor
    from .reporter import Reporter as PReporter

    return PipelineConfig(
        preprocess=ProducerConfig.fromProducer(PPreprocessor),
        extractor=ProducerConfig.fromProducer(PExtractor),
        differ=ProducerConfig.fromProducer(PDiffer),
        evaluator=ProducerConfig.fromProducer(PEvaluator),
        reporter=ProducerConfig.fromProducer(PReporter),
    )
