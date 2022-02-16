from aexpy import setCacheDirectory, initializeLogging
import sys
from pathlib import Path
import logging

# sys.path.append(str(Path(__file__).parent.parent.resolve()))

initializeLogging(logging.WARNING)

setCacheDirectory((Path(__file__).parent.parent.parent / "exps").resolve())
