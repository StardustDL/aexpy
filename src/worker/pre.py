import sys
from aexpy.models import Release
from aexpy.preprocessing import getDefault
from aexpy.preprocessing.default import Preprocessor as VersionGetter
from aexpy.utils import ensureDirectory, TeeFile
from . import getCache

worker = getDefault()

worker.cache = getCache() / worker.stage()
ensureDirectory(worker.cache)

versionGetter = VersionGetter(redo=True)

logout = (worker.cache / "worker.log").open("w")

out = TeeFile(sys.stdout, logout)


projects = ["urllib3", "python-dateutil", "requests", "pyyaml", "jmespath",
            "numpy", "click", "pandas", "flask", "tornado", "django", "scrapy", "coxbuild"]

for project in projects:
    print(f"Work {project}...", file=out)
    versions = list(versionGetter.getReleases(project).keys())
    success = 0
    for i, version in enumerate(versions):
        rel = Release(project, version)
        print(f"  Preprocess ({i+1}/{len(versions)}) {rel}...", file=out)
        try:
            dist = worker.preprocess(rel)
            success += 1
            print(f"    Finish {rel}: {dist}", file=out)
        except Exception as e:
            print(f"    Error {rel}: {e}", file=out)

    print(f"  Done {project}: {success}/{len(versions)}", file=out)

logout.close()

"""
Done urllib3: 43/71
Done python-dateutil: 19/32
Done requests: 65/145
Done pyyaml: 6/36
Done jmespath: 9/24
Done numpy: 93/115
Done click: 42/44
Done pandas: 49/85
Done flask: 23/41
Done tornado: 3/62
Done django: 235/294
Done scrapy: 39/83

626/1032 release
"""