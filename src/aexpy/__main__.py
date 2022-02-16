from email.policy import default
import json
import logging
import pathlib
import time

import click
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

import code

from .pipelines import Pipeline, EmptyPipeline
from .models import Release

from . import __version__, initializeLogging, setCacheDirectory


pipeline: "Pipeline" = EmptyPipeline()
interactMode: "bool" = False


@click.group()
@click.pass_context
@click.option("-c", "--cache", type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path), default="cache", help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 4))
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
def main(ctx=None, cache: pathlib.Path = "cache", verbose: int = 0, interact: bool = False, redo: bool = False) -> None:
    """Aexpy (https://github.com/StardustDL/aexpy)"""

    global pipeline, interactMode

    interactMode = interact

    loggingLevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
        4: logging.NOTSET
    }[verbose]

    initializeLogging(loggingLevel)

    logger = logging.getLogger("Cli-Main")

    logger.debug(f"Logging level: {loggingLevel}")

    if isinstance(cache, str):
        cache = pathlib.Path(cache)

    setCacheDirectory(cache)

    pipeline = Pipeline(redo=redo)


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def pre(project: str, version: str, redo: bool = False):
    """Preprocess a release."""
    release = Release(project, version)
    result = pipeline.preprocess(release, redo=redo if redo else None)
    assert result.success
    print(f"File: {result.wheelFile}")

    if interactMode:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def ext(project: str, version: str, redo: bool = False):
    """Extract the API in a release."""
    release = Release(project, version)
    result = pipeline.extract(release, redo=redo if redo else None)
    assert result.success
    print(f"APIs: {len(result.entries)}")

    if interactMode:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def dif(project: str, old: str, new: str, redo: bool = False):
    """Diff two releases."""
    old = Release(project, old)
    new = Release(project, new)
    result = pipeline.diff(old, new, redo=redo if redo else None)
    assert result.success
    print(f"Changes: {len(result.entries)}")

    if interactMode:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def eva(project: str, old: str, new: str, redo: bool = False):
    """Evaluate differences between two releases."""
    old = Release(project, old)
    new = Release(project, new)
    result = pipeline.eval(old, new, redo=redo if redo else None)
    assert result.success
    print(f"Changes: {len(result.entries)}")

    if interactMode:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def rep(project: str, old: str, new: str, redo: bool = False) -> None:
    """Report breaking changes between two releases."""
    old = Release(project, old)
    new = Release(project, new)
    result = pipeline.report(old, new, redo=redo if redo else None)
    assert result.success
    print(f"File: {result.file}")

    if interactMode:
        code.interact(banner="", local=locals())


main.add_command(pre)
main.add_command(ext)
main.add_command(dif)
main.add_command(eva)
main.add_command(rep)


if __name__ == '__main__':
    main()
