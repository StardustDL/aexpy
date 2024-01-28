from datetime import datetime
import os
import shutil
import subprocess
from coxbuild.schema import task, group, named, run, depend, ext
from coxbuild.extensions.python import docs as pydocs
from coxbuild.extensions.python import format as pyformat
from coxbuild.extensions.python import package as pypackage
from coxbuild.extensions.python import test as pytest
from pathlib import Path

ext(pydocs)
ext(pyformat)
ext(pypackage)
ext(pytest)

@buildGroup
@named("docker")
@task
def build_docker():
    try:
        commit = subprocess.check_output(
            "git rev-parse HEAD".split(), text=True).strip()
    except:
        commit = "unknown"
    run(["docker", "build", "--build-arg", f"GIT_COMMIT={commit}", "--build-arg",
        f"BUILD_DATE={datetime.now().isoformat()}", "-t", "aexpy/aexpy", "."])
    run(["docker", "tag", "aexpy/aexpy",
        "registry.us-west-1.aliyuncs.com/aexpy/aexpy:latest"])
