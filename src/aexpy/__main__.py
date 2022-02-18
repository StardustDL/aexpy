from dataclasses import dataclass
from datetime import datetime, timedelta
from email.policy import default
import json
import logging
from optparse import Option
import os
import pathlib
import time
from aexpy.utils import elapsedTimer

import click
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

import yaml

import code

from .pipelines import Pipeline, EmptyPipeline
from .models import Release

from . import __version__, initializeLogging, setCacheDirectory
from .env import env, getPipeline


@click.group()
@click.pass_context
@click.option("-c", "--cache", type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path), default="cache", help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 5), help="Increase verbosity.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
@click.option("-p", "--provider", type=click.Choice(["default", "pidiff", "pycompat"]), default="default", help="Provider to use.")
@click.option("--pipeline", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-pipeline.yml", help="Pipeline file.", envvar="AEXPY_PIPELINE")
@click.option("--config", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-config.yml", help="Config file.", envvar="AEXPY_CONFIG")
def main(ctx=None, cache: pathlib.Path = "cache", verbose: int = 0, interact: bool = False, redo: bool = False, no_cache: bool = False, provider: "str" = "default", pipeline: pathlib.Path = "aexpy-pipeline.yml", config: pathlib.Path = "aexpy-config.yml") -> None:
    """Aexpy (https://github.com/StardustDL/aexpy)"""

    env.interact = interact
    if redo:
        env.redo = redo
    if no_cache:
        env.cached = not no_cache

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
    if isinstance(pipeline, str):
        pipeline = pathlib.Path(pipeline)
    if isinstance(config, str):
        config = pathlib.Path(config)

    setCacheDirectory(cache)

    loadedPipeline = False

    if pipeline.exists() and pipeline.is_file():
        try:
            data = yaml.safe_load(pipeline.read_text())
            env.loadProvider(data)
            loadedPipeline = True
        except Exception as ex:
            raise BadOptionUsage(f"Invalid pipeline file: {pipeline}") from ex
    
    if config.exists() and config.is_file():
        try:
            data = yaml.safe_load(config.read_text())
            env.loadConfig(data)
        except Exception as ex:
            raise BadOptionUsage(f"Invalid config file: {config}") from ex

    if not loadedPipeline:
        match provider:
            case "default":
                pass
            case "pidiff":
                from .third.pidiff.pipeline import getDefault
                env.provider = getDefault()
            case "pycompat":
                from .third.pycompat.pipeline import getDefault
                env.provider = getDefault()


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def pre(project: str, version: str, redo: bool = False, no_cache: bool = False):
    """Preprocess a release."""
    release = Release(project, version)
    pipeline = getPipeline()
    result = pipeline.preprocess(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(f"File: {result.wheelFile}")

    if env.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def ext(project: str, version: str, redo: bool = False, no_cache: bool = False):
    """Extract the API in a release."""
    release = Release(project, version)
    pipeline = getPipeline()
    result = pipeline.extract(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(f"APIs: {len(result.entries)}")

    if env.interact:
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
    pipeline = getPipeline()
    result = pipeline.diff(old, new, redo=redo if redo else None,
                                   cached=not no_cache if no_cache else None)
    assert result.success
    print(f"Changes: {len(result.entries)}")

    if env.interact:
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
    pipeline = getPipeline()
    result = pipeline.eval(old, new, redo=redo if redo else None,
                                   cached=not no_cache if no_cache else None)
    assert result.success
    print(f"Changes: {len(result.entries)}")

    if env.interact:
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
    pipeline = getPipeline()
    result = pipeline.report(
        old, new, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(f"File: {result.file}")

    if env.interact:
        code.interact(banner="", local=locals())


@click.command()
@click.argument("projects", default=None, nargs=-1)
@click.option("-s", "--stage", type=click.Choice(["pre", "ext", "dif", "eva", "rep", "ana", "all", "bas", "clr"]), default="all", help="Stage to run.")
def bat(projects: "list[str] | None" = None, stage: "str" = "all") -> None:
    """Run a batch of stages."""
    from .batch.single import SingleProcessor
    from .batch.pair import PairProcessor

    projects = list(projects or [])

    from .batch import default

    with elapsedTimer() as elapsed:
        print(
            f"Running {stage} on {len(projects)} projects: {projects} @ {datetime.now()}.\n")
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
                from aexpy.extracting.environments.default import DefaultEnvironment
                DefaultEnvironment.clearBase()

                from aexpy.third.pycompat.extractor import PycompatEnvironment
                PycompatEnvironment.clearBase()

                if not os.getenv("RUN_IN_DOCKER"):
                    from aexpy.third.pidiff.evaluator import Evaluator
                    Evaluator.clearBase()
            case "bas":
                from aexpy.extracting.environments.default import DefaultEnvironment
                DefaultEnvironment.buildAllBase()

                from aexpy.third.pycompat.extractor import PycompatEnvironment
                PycompatEnvironment.buildAllBase()

                if not os.getenv("RUN_IN_DOCKER"):
                    from aexpy.third.pidiff.evaluator import Evaluator
                    Evaluator.buildAllBase()
        print(
            f"\nFinished {stage} on {len(projects)} projects in {timedelta(seconds=elapsed())}: {projects} @ {datetime.now()}.")


main.add_command(pre)
main.add_command(ext)
main.add_command(dif)
main.add_command(eva)
main.add_command(rep)
main.add_command(bat)


if __name__ == '__main__':
    main()
