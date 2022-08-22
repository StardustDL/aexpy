from aexpy.reporting.text import TextReporter
from .differ import CombinedDiffer
from .extractor import Extractor
from aexpy.batching import InProcessBatcher


class PycompatService(Extractor, CombinedDiffer, TextReporter, InProcessBatcher):
    pass
