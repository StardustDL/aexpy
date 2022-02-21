from datetime import datetime, timedelta
import subprocess
import sys
import os
from pathlib import Path
import click

defaultProjects = ["urllib3", "python-dateutil", "requests", "pyyaml", "jmespath",
                   "numpy", "click", "pandas", "flask", "tornado", "django", "scrapy", "coxbuild", "schemdule"]
providers = ["default", "pidiff", "pycompat"]

root = Path(__file__).parent.parent.resolve()
logroot = (root / "logs").resolve()
cacheroot = (root.parent / "exps").resolve()


def getcmdpre(docker: "str" = ""):
    if docker:
        return ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", "-v", f"{str(cacheroot)}:/data", "aexpy"]
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

            result = subprocess.run(
                [*cmdpre, "-p", provider, "pro", project, *workercmd], stderr=subprocess.STDOUT, stdout=f)

        if result.returncode != 0:
            print(
                f"Failed to process {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}, duration: {elapsed()}, logfile: {logfile}.")
        else:
            print(
                f"Processed {project} by {provider} ({'Docker' if docker else 'Normal'}) @ {datetime.now()}, duration: {elapsed()}, logfile: {logfile}.")


def processAll(projects: "list[str]", provider: "str" = "default", docker: "str" = "", worker: "int | None" = None):
    for project in projects:
        process(project, provider, docker, worker)


def processAllProvider(projects: "list[str]", docker: "str" = "", worker: "int | None" = None):
    for provider in providers:
        processAll(projects, provider, docker, worker)


@click.command()
@click.option("-p", "--provider", type=click.Choice([*providers, "all"]), default="pidiff", help="Provider.")
@click.option("-w", "--worker", type=int, default=None, help="Number of workers.")
@click.option("-d", "--docker", is_flag=True, default=False, help="Docker.")
@click.argument("projects", default=None, nargs=-1)
def main(projects: "list[str] | None" = None, provider: "str" = "all", docker: "bool" = False, worker: "int | None" = None):
    sys.path.append(str(root))

    print(f"Root path: {root}")
    print(f"Log path: {logroot}")
    print(f"Cache path: {cacheroot}")

    projects = projects or []

    if "all" in projects:
        projects = defaultProjects

    if provider == "all":
        processAllProvider(projects, "aexpy" if docker else "", worker)
    else:
        processAll(projects, provider, "aexpy" if docker else "", worker)


if __name__ == "__main__":
    main()
