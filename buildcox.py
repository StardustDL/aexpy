from pathlib import Path
from coxbuild.schema import task, group, named, run, depend, ext, withExecutionState, ExecutionState
from coxbuild.extensions.python import format as pyformat, package as pypackage


ext("file://build.py")
ext("file://data.py")


@depend(pyformat.format)
@task
def format():
    pass


@depend(pypackage.restore)
@task
def restore():
    pass


@named("run")
@withExecutionState
@task
def runexe(executionState: "ExecutionState"):
    run(["python", "-u", "-m", "aexpy", "-c", "../../aexpy-exps",
        *executionState.unmatchedTasks], cwd=Path("src"))
