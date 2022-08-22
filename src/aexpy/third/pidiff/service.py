from aexpy.reporting.text import TextReporter
from .differ import Evaluator
from aexpy.batching import InProcessBatcher


class PidiffService(Evaluator, TextReporter, InProcessBatcher):
    pass
