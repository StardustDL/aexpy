import shutil
from coxbuild.schema import task, group, named, run, depend
from coxbuild.extensions.python import format as pyformat, package as pypackage
from pathlib import Path


buildGroup = group("build")


@buildGroup
@named("docker")
@task
def build_docker():
    run(["docker", "build", "-t", "aexpy/aexpy", "."])


@buildGroup
@named("base")
@task
def build_base():
    run(["python", "-u", "-m", "aexpy", "prepare"], cwd=Path("src"))


@buildGroup
@named("web")
@task
def build_web():
    run(["npm", "run", "build"], cwd=Path("src").joinpath("web"))
    shutil.copytree(Path("src") / "web" / "dist", Path("src") /
                    "aexpy"/"serving"/"server"/"wwwroot")


@buildGroup
@task
def clean():
    run(["python", "-u", "-m", "aexpy", "prepare", "-c"], cwd=Path("src"))
