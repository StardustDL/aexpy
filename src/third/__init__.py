import sys
from pathlib import Path
import logging

from aexpy import setCacheDirectory, initializeLogging

initializeLogging(logging.WARNING)

# sys.path.append(str(Path(__file__).parent.parent.resolve()))

setCacheDirectory((Path(__file__).parent.parent.parent / "exps").resolve())