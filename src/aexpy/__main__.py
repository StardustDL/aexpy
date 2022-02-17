from dataclasses import dataclass
from email.policy import default
import json
import logging
from optparse import Option
import pathlib
import time

import click
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

import code

from .pipelines import Pipeline, EmptyPipeline
from .models import Release

from . import __version__, initializeLogging, setCacheDirectory


@dataclass
class Options:
    pipeline: "Pipeline" = EmptyPipeline()
    interact: "bool" = False
    provider: "str" = "default"


options = Options()


@click.group()
@click.pass_context
@click.option("-c", "--cache", type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path), default="cache", help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 5), help="Increase verbosity.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
@click.option("-p", "--provider", type=click.Choice(["default", "pidiff", "pycompat"]), default="default", help="Provider to use.")
def main(ctx=None, cache: pathlib.Path = "cache", verbose: int = 0, interact: bool = False, redo: bool = False, no_cache: bool = False, provider: "str" = "default") -> None:
    """Aexpy (https://github.com/StardustDL/aexpy)"""

    options.interact = interact

    loggingLevel = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.NOTSET
    }[verbose]

    initializeLogging(loggingLevel)

    logger = logging.getLogger("Cli-Main")

    logger.debug(f"Logging level: {loggingLevel}")

    if isinstance(cache, str):
        cache = pathlib.Path(cache)

    setCacheDirectory(cache)

    options.provider = provider

    match options.provider:
        case "default":
            options.pipeline = Pipeline(redo=redo, cached=not no_cache)
        case "pidiff":
            from .third.pidiff.pipeline import Pipeline as PidiffPipeline
            options.pipeline = PidiffPipeline(redo=redo, cached=not no_cache)
        case "pycompat":
            from .third.pycompat.pipeline import Pipeline as PycompatPipeline
            options.pipeline = PycompatPipeline(redo=redo, cached=not no_cache)


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def pre(project: str, version: str, redo: bool = False, no_cache: bool = False):
    """Preprocess a release."""
    release = Release(project, version)
    result = options.pipeline.preprocess(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(f"File: {result.wheelFile}")

    if options.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def ext(project: str, version: str, redo: bool = False, no_cache: bool = False):
    """Extract the API in a release."""
    release = Release(project, version)
    result = options.pipeline.extract(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(f"APIs: {len(result.entries)}")

    if options.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def dif(project: str, old: str, new: str, redo: bool = False, no_cache: bool = False):
    """Diff two releases."""
    old = Release(project, old)
    new = Release(project, new)
    result = options.pipeline.diff(old, new, redo=redo if redo else None,
                                   cached=not no_cache if no_cache else None)
    assert result.success
    print(f"Changes: {len(result.entries)}")

    if options.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def eva(project: str, old: str, new: str, redo: bool = False, no_cache: bool = False):
    """Evaluate differences between two releases."""
    old = Release(project, old)
    new = Release(project, new)
    result = options.pipeline.eval(old, new, redo=redo if redo else None,
                                   cached=not no_cache if no_cache else None)
    assert result.success
    print(f"Changes: {len(result.entries)}")

    if options.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def rep(project: str, old: str, new: str, redo: bool = False, no_cache: bool = False) -> None:
    """Report breaking changes between two releases."""
    old = Release(project, old)
    new = Release(project, new)
    result = options.pipeline.report(
        old, new, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(f"File: {result.file}")

    if options.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("projects", default=None, nargs=-1)
@click.option("-s", "--stage", type=click.Choice(["pre", "ext", "dif", "eva", "rep", "ana", "all", "bas", "clr"]), default="all", help="Stage to run.")
def bat(projects: "list[str] | None" = None, stage: "str" = "all") -> None:
    """Run a batch of stages."""
    from .batch.single import SingleProcessor
    from .batch.pair import PairProcessor

    projects = list(projects or [])

    match options.provider:
        case "default":
            from .batch import default
        case "pidiff":
            from .batch import pidiff as default
        case "pycompat":
            from .batch import pycompat as default
    match stage:
        case "pre":
            SingleProcessor(default.pre).processProjects(
                projects, parallel=False)
        case "ext":
            SingleProcessor(default.ext).processProjects(
                projects, parallel=False)
        case "dif":
            PairProcessor(default.dif).processProjects(
                projects, parallel=False)
        case "eva":
            PairProcessor(default.eva).processProjects(
                projects, parallel=False)
        case "rep":
            PairProcessor(default.rep).processProjects(
                projects, parallel=False)
        case "ana":
            SingleProcessor(default.ext).processProjects(
                projects, parallel=False)
            PairProcessor(default.dif).processProjects(
                projects, parallel=False)
            PairProcessor(default.eva).processProjects(
                projects, parallel=False)
            PairProcessor(default.rep).processProjects(
                projects, parallel=False)
        case "all":
            SingleProcessor(default.pre).processProjects(
                projects, parallel=False)
            SingleProcessor(default.ext).processProjects(
                projects, parallel=False)
            PairProcessor(default.dif).processProjects(
                projects, parallel=False)
            PairProcessor(default.eva).processProjects(
                projects, parallel=False)
            PairProcessor(default.rep).processProjects(
                projects, parallel=False)
        case "clr":
            from aexpy.extracting.environments.conda import CondaEnvironment
            CondaEnvironment.clearBase()

            from aexpy.third.pidiff.evaluator import Evaluator
            Evaluator.clearBase()
        case "bas":
            from aexpy.extracting.environments.conda import CondaEnvironment
            CondaEnvironment.buildAllBase()

            from aexpy.third.pidiff.evaluator import Evaluator
            Evaluator.buildAllBase()


main.add_command(pre)
main.add_command(ext)
main.add_command(dif)
main.add_command(eva)
main.add_command(rep)
main.add_command(bat)


if __name__ == '__main__':
    main()
