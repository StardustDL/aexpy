import code
import json
import logging
import os
import pathlib
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.policy import default
from optparse import Option

import click
import yaml
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

from aexpy.utils import elapsedTimer

from . import __version__, initializeLogging, setCacheDirectory
from .env import PipelineConfig, env, getPipeline
from .models import Release, ReleasePair
from .pipelines import EmptyPipeline, Pipeline


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    def resolve_command(self, ctx, args):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args


@click.command(cls=AliasedGroup)
@click.pass_context
@click.version_option(__version__, package_name="aexpy", prog_name="aexpy", message="%(prog)s v%(version)s, written by StardustDL.")
@click.option("-c", "--cache", type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=pathlib.Path), default="cache", help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 5), help="Increase verbosity.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
@click.option("-p", "--provider", type=click.Choice(["default", "pidiff", "pycompat"]), default="default", help="Provider to use.")
@click.option("--pipeline", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-pipeline.yml", help="Pipeline file.", envvar="AEXPY_PIPELINE")
@click.option("--config", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-config.yml", help="Config file.", envvar="AEXPY_CONFIG")
def main(ctx=None, cache: pathlib.Path = "cache", verbose: int = 0, interact: bool = False, redo: bool = False, only_cache: "bool" = False, no_cache: bool = False, provider: "str" = "default", pipeline: pathlib.Path = "aexpy-pipeline.yml", config: pathlib.Path = "aexpy-config.yml") -> None:
    """
    Aexpy (https://github.com/StardustDL/aexpy)

    Aexpy /eɪkspaɪ/ is an Api EXplorer in PYthon.
    """

    if isinstance(cache, str):
        cache = pathlib.Path(cache)
    if isinstance(pipeline, str):
        pipeline = pathlib.Path(pipeline)
    if isinstance(config, str):
        config = pathlib.Path(config)

    env.interact = interact

    env.verbose = verbose
    env.cache = cache

    env.prepare()

    logger = logging.getLogger("Cli-Main")

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
                env.provider = PipelineConfig()
            case "pidiff":
                from .third.pidiff.pipeline import getDefault
                env.provider = getDefault()
            case "pycompat":
                from .third.pycompat.pipeline import getDefault
                env.provider = getDefault()

    if redo:
        env.provider.redo = redo
    if no_cache:
        env.provider.cached = not no_cache
    if only_cache:
        env.provider.onlyCache = only_cache


@main.command()
@click.argument("release")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def preprocess(release: str, redo: bool = False, no_cache: bool = False, only_cache: "bool" = False):
    """Preprocess a release, project@version ."""
    release = Release.fromId(release)
    pipeline = getPipeline()
    result = pipeline.preprocess(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("release")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def extract(release: "str", redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False):
    """Extract the API in a release, project@version ."""
    release = Release.fromId(release)
    pipeline = getPipeline()
    result = pipeline.extract(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def diff(pair: "str", redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False):
    """Diff two releases, project@version1:version2 or project1@version1:project2@version2 ."""
    pair = ReleasePair.fromId(pair)
    pipeline = getPipeline()
    result = pipeline.diff(pair, redo=redo if redo else None,
                           cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def evaluate(pair: "str", redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False):
    """Evaluate differences between two releases, project@version1:version2 or project1@version1:project2@version2 ."""
    pair = ReleasePair.fromId(pair)
    pipeline = getPipeline()
    result = pipeline.eval(pair, redo=redo if redo else None,
                           cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("-R", "--reall", is_flag=True, default=False, help="Redo diff, eval and report.")
def report(pair: "str", redo: "bool" = False, no_cache: "bool" = False, reall: "bool" = False, only_cache: "bool" = False) -> None:
    """Report breaking changes between two releases, project@version1:version2 or project1@version1:project2@version2 ."""
    pair = ReleasePair.fromId(pair)
    pipeline = getPipeline()

    if reall:
        redo = True
        result = pipeline.diff(pair, redo=redo if redo else None,
                               cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
        assert result.success
        result = pipeline.eval(pair, redo=redo if redo else None,
                               cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
        assert result.success

    result = pipeline.report(
        pair, redo=redo if redo else None, cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)
    assert result.success
    print(result.file.read_text())

    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("project")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("-w", "--workers", type=int, default=None, help="Number of workers.")
@click.option("-t", "--retry", default=3, help="Number of retries.")
def batch(project: "str", workers: "int | None" = None, retry: "int" = 3, redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False) -> None:
    """Process project."""
    pipeline = getPipeline()

    result = pipeline.batch(
        project, workers, retry, redo=redo if redo else None, cached=not no_cache if no_cache else None, onlyCache=only_cache if only_cache else None)

    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.option("-c", "--clear", is_flag=True, help="Clear the created environment.")
def rebuild(clear: "bool" = False):
    """Rebuild the environment."""
    if clear:
        from aexpy.extracting.environments.default import DefaultEnvironment
        DefaultEnvironment.clearEnv()

        from aexpy.third.pycompat.extractor import PycompatEnvironment
        PycompatEnvironment.clearEnv()

        return

    from aexpy.extracting.environments.default import DefaultEnvironment
    DefaultEnvironment.clearBase()
    DefaultEnvironment.buildAllBase()

    from aexpy.third.pycompat.extractor import PycompatEnvironment
    PycompatEnvironment.clearBase()
    PycompatEnvironment.buildAllBase()

    if not os.getenv("RUN_IN_DOCKER"):
        from aexpy.third.pidiff.evaluator import Evaluator
        Evaluator.clearBase()
        Evaluator.buildAllBase()


if __name__ == '__main__':
    main()
