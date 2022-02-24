import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

defaultProjects = ["urllib3", "python-dateutil", "requests", "pyyaml", "jmespath", "click",
                   "coxbuild", "schemdule", "flask", "tornado", "scrapy", "numpy", "pandas", "django"]

cacheRoot = Path("summary-logs")