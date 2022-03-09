from coxbuild.schema import task, group, named, run, depend
from coxbuild.extensions.python import format as pyformat, package as pypackage


testGroup = group("test")


@testGroup
@named("docker")
@task
def test_docker():
    run(["docker", "run", "--rm", "-it", "-v",
        "/var/run/docker.sock:/var/run/docker.sock", "aexpy/aexpy", "--help"])
    run(["docker", "run", "--rm", "-it", "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "aexpy/aexpy", "-p", "pidiff", "rep", "more-executors@1.15.0:1.16.0"])
    run(["docker", "run", "--rm", "-it", "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "aexpy/aexpy", "-p", "pycompat", "rep", "more-executors@1.15.0:1.16.0"])
    run(["docker", "run", "--rm", "-it", "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "aexpy/aexpy", "rep", "more-executors@1.15.0:1.16.0"])


@testGroup
@named("base")
@task
def test_base():
    run(["python", "-u", "-m", "aexpy", "retest"])


@testGroup
@task
def clean():
    run(["python", "-u", "-m", "aexpy", "prepare", "-c"])
