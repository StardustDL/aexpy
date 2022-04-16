from pathlib import Path
import shutil
from coxbuild.schema import task, group, named, run, depend, ext, withConfig, Configuration, beforePipeline
import subprocess
from datetime import datetime
import sys

dataGroup = group("data")

allProjects = ["urllib3", "python-dateutil", "requests", "PyYAML", "jmespath", "click",
               "coxbuild", "schemdule", "Flask", "tornado", "Scrapy", "Jinja2"]
largeProjects = ["numpy", "pandas", "Django", "matplotlib"]
groundProjects = ["resolvelib", "asyncpg", "streamz", "python-binance",
                  "ao3-api", "PyJWT", "pystac", "evidently", "pyoverkiz",
                  "paramiko", "prompt_toolkit", "betfairlightweight",
                  "pecanpy", "pooch", "appcenter", "meshio", "gradio", 
                  "astroquery", "stonesoup", "clyngor", "captum",
                  "trio", "bentoml", "rpyc", "catkin_tools", 
                  "xarray", "humanize", "markupsafe", "docspec-python",
                  "harvesters", "diffsync"]
# allProjects += groundProjects
providers = ["pidiff", "pycompat", "default", "pycg"]

root = Path("src").resolve()
logroot = Path("logs").resolve()
cacheroot = root.parent.parent.joinpath("aexpy-exps").resolve()


@beforePipeline
def before(*args, **kwds):
    sys.path.append(str(root))


def getcmdpre(docker: "str" = ""):
    if docker:
        return ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", "-v", f"{str(cacheroot)}:/data", "-m", "50g", "--name", "aexpy-data-pro",  "aexpy/aexpy"]
    else:
        return ["python", "-u", "-m", "aexpy", "-c", str(cacheroot)]


def process(project: "str", provider: "str" = "default", docker: "str" = "", worker: "int | None" = None):
    print(
        f"Processing {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}")

    from aexpy.utils import ensureDirectory, elapsedTimer

    cmdpre = getcmdpre(docker)

    logfile = logroot / provider / f"{project}.log"

    ensureDirectory(logfile.parent)

    with elapsedTimer() as elapsed:
        with logfile.open("w") as f:
            if worker:
                workercmd = ["-w", str(worker)]
            else:
                workercmd = []

            try:
                result = subprocess.run(
                    [*cmdpre, "-p", provider, "batch", project, *workercmd, "-r"], stderr=subprocess.STDOUT, stdout=f, cwd=root, timeout=10 * 60 * 60)
            except subprocess.TimeoutExpired:
                result = None

        if result is None:
            print(
                f"Timeout to process {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}, duration: {elapsed()}, logfile: {logfile} .")
        elif result.returncode != 0:
            print(
                f"Failed to process {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}, duration: {elapsed()}, logfile: {logfile} .")
        else:
            print(
                f"Processed {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}, duration: {elapsed()}, logfile: {logfile} .")
            try:
                result = subprocess.run(
                    [*cmdpre, "-p", provider, "index", project, *workercmd, "-r"], cwd=root, timeout=2 * 60 * 60)
                if result.returncode != 0:
                    print(
                        f"Failed to index {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}")
                else:
                    print(
                        f"Indexed {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}")
            except subprocess.TimeoutExpired:
                print(
                    f"Timeout to index {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}")


def processAll(projects: "list[str]", provider: "str" = "default", docker: "str" = "", worker: "int | None" = None):
    for project in projects:
        process(project, provider, docker, worker)


@dataGroup
@withConfig
@task
def work(config: "Configuration"):
    print(f"Root: {root}")
    print(f"Cache Directory: {cacheroot}")
    print(f"Log Directory: {logroot}")

    provider = config.get("provider") or "default"
    project = config.get("project")
    worker = config.get("worker") or None
    docker = config.get("docker") or ""
    projects = [project] if project else []

    if worker is not None:
        worker = int(worker)

    if "all" in projects:
        projects = allProjects

    if "large" in projects:
        projects = largeProjects

    if "ground" in projects:
        projects = groundProjects

    if "full" in projects:
        projects = allProjects + groundProjects

    if provider == "all":
        for provider in providers:
            processAll(projects, provider, docker, worker)
    else:
        processAll(projects, provider, docker, worker)


stages = ["extracting", "differing", "evaluating",
          "reporting", "batching/inprocess", "batching/index"]
third = ["pidiff", "pycompat", "pycg"]


@dataGroup
@task
def clean():
    for stage in stages:
        path = cacheroot / stage
        if not path.exists():
            continue
        for item in path.glob("*"):
            if item.stem in third:
                continue
            print(f"Cleaning {item}")
            run(["sudo", "rm", "-rf", str(item.resolve())])


@dataGroup
@task
def cleanthird():
    for stage in stages:
        for item in third:
            path = cacheroot / stage / item
            if not path.exists():
                continue
            print(f"Cleaning {path}")
            run(["sudo", "rm", "-rf", str(path.resolve())])


@dataGroup
@depend(clean, cleanthird)
@task
def cleanall():
    pass


@dataGroup
@task
def clear():
    print(f"Cleaning {cacheroot}")
    run(["sudo", "rm", "-rf", str(cacheroot.resolve())])


@dataGroup
@task
def tar():
    run(["sudo", "tar", "czvf", "data.tar.gz", "preprocessing/results", "batching", "differing",
        "evaluating", "extracting", "reporting"], cwd=cacheroot)
