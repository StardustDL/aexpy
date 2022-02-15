import logging
import sys
from aexpy.models import Release
from aexpy.preprocessing import getDefault
from aexpy.preprocessing.default import Preprocessor as VersionGetter
from aexpy.utils import ensureDirectory, TeeFile
from . import projects

worker = getDefault()

versionGetter = VersionGetter(redo=True)

logout = (worker.cache / "worker.log").open("w")

out = TeeFile(sys.stdout, logout)

result = {}

for project in projects:
    print(f"Work {project}...", file=out)
    versions = list(versionGetter.getReleases(project).keys())
    success = 0
    for i, version in enumerate(versions):
        rel = Release(project, version)
        print(f"  Preprocess ({i+1}/{len(versions)}) {rel}...", file=out)
        try:
            dist = worker.preprocess(rel)
            if dist.success:
                success += 1
                print(f"    Finish {rel}: {dist}", file=out)
            else:
                print(f"    Failed {rel}: {dist}", file=out)
        except Exception as e:
            print(f"    Error {rel}: {e}", file=out)

    print(f"  Done {project}: {success}/{len(versions)}", file=out)
    result[project] = (success, len(versions))

print(f"\nDone:", file=out)
for key, value in result.items():
    print(f"  {key}: {value[0]}/{value[1]}", file=out)

print(f"Releases: {sum((v[0] for v in result.values()))}/{sum((v[1] for v in result.values()))}", file=out)

logout.close()
