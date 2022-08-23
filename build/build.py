import os
import shutil
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

buildGroup = group("build")
deployGroup = group("deploy")

readmeDst = Path("./src/README.md")


@pypackage.build.setup
def setupBuild(*args, **kwds):
    shutil.copyfile(Path("README.md"), readmeDst)


@pypackage.build.teardown
def teardownBuild(*args, **kwds):
    os.remove(readmeDst)


@depend(pydocs.apidoc)
@task
def docs(): pass


@depend(pypackage.deploy)
@deployGroup
@named("package")
@task
def deploy(): pass


@depend(pypackage.restore, pypackage.build)
@buildGroup
@named("package")
@task
def build(): pass


@depend(pypackage.installBuilt)
@task
def installBuilt(): pass


@buildGroup
@named("exps")
@task
def build_docker_exps():
    run(["docker", "build", "-t", "aexpy/exps", "-f", "exps/Dockerfile.exps", "."])


@buildGroup
@named("docker")
@task
def build_docker():
    run(["docker", "build", "-t", "aexpy/aexpy", "."])
    run(["docker", "tag", "aexpy/aexpy",
        "registry.us-west-1.aliyuncs.com/aexpy/aexpy:latest"])


@buildGroup
@named("base")
@task
def build_base():
    run(["python", "-u", "-m", "aexpy", "initialize"], cwd=Path("src"))


@buildGroup
@named("web")
@task
def build_web():
    run(["npm", "ci"], cwd=Path("src").joinpath("web"))
    run(["npm", "run", "build"], cwd=Path("src").joinpath("web"))
    shutil.copytree(Path("src") / "web" / "dist", Path("src") /
                    "aexpy"/"serving"/"server"/"wwwroot")


@buildGroup
@task
def clean():
    run(["python", "-u", "-m", "aexpy", "initialize", "-c"], cwd=Path("src"))
