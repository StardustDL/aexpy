from aexpy import setCacheDirectory, initializeLogging
import sys
from pathlib import Path
import logging

# sys.path.append(str(Path(__file__).parent.parent.resolve()))

initializeLogging(logging.WARNING)

projects = ["urllib3", "python-dateutil", "requests", "pyyaml", "jmespath",
            "numpy", "click", "pandas", "flask", "tornado", "django", "scrapy", "coxbuild"]

setCacheDirectory((Path(__file__).parent.parent.parent / "exps").resolve())
