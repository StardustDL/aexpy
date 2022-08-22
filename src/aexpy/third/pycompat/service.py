from aexpy.reporting.text import TextReporter
from .differ import CombinedDiffer
from .extractor import Extractor


class PycompatService(Extractor, CombinedDiffer, TextReporter):
    pass
