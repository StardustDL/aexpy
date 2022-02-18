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

from datetime import datetime, timedelta
import json
from typing import Callable
import subprocess


def getDefault() -> "PipelineConfig":
    from aexpy.preprocessing import Empty as EPreprocessor
    from aexpy.extracting import Empty as EExtractor
    from aexpy.differing import Empty as EDiffer
    from .evaluator import Evaluator as PEvaluator
    from .reporter import Reporter as PReporter

    return PipelineConfig(
        preprocess=ProducerConfig.fromProducer(EPreprocessor),
        extractor=ProducerConfig.fromProducer(EExtractor),
        differ=ProducerConfig.fromProducer(EDiffer),
        evaluator=ProducerConfig.fromProducer(PEvaluator),
        reporter=ProducerConfig.fromProducer(PReporter),
    )
