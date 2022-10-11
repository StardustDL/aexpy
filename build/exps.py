from pathlib import Path
from coxbuild.schema import task, group, named, run, depend, ext, withExecutionState, ExecutionState, withProject, ProjectSettings
from coxbuild.extensions.python import format as pyformat, package as pypackage


@named("build:exps")
@task
def build_docker_exps():
    run(["docker", "build", "-t", "aexpy/exps", "-f", "exps/Dockerfile.exps", "."])


@named("serve:exps")
@task
def serve_exps():
    run(["docker", "run", "--rm", "-d",
         "-p", "50036:8008",
         "-v", "/var/run/docker.sock:/var/run/docker.sock",
         "-v", "/home/test/liang/aexpy-exps:/data",
         "-m", "20g",
         "--name", "aexpy",
         "aexpy/exps", "-vv",
         "serve", "-d", 
         "-u", "star", "-P", "truth"])
