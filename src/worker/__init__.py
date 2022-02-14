import sys
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).parent.parent.resolve()))

logging.basicConfig(level=logging.WARNING)


def getCache():
    return (Path(__file__).parent.parent / "exps").resolve()
