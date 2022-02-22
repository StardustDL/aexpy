from pathlib import Path
from coxbuild.schema import task, group, named, run, depend, ext, withExecutionState, ExecutionState, withProject, ProjectSettings
from coxbuild.extensions.python import format as pyformat, package as pypackage


ext("file://build/build.py")
ext("file://build/data.py")
ext("file://build/test.py")

@depend(pyformat.restore)
@withProject
@task
async def format(project: "ProjectSettings"):
    await pyformat.autopep8(project.src)
    await pyformat.isort(project.src)


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
