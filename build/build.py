from coxbuild.schema import task, group, named, run, depend
from coxbuild.extensions.python import format as pyformat, package as pypackage


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
    run(["python", "-u", "-m", "aexpy", "rebuild"])


@buildGroup
@task
def clean():
    run(["python", "-u", "-m", "aexpy", "rebuild", "-c"])
