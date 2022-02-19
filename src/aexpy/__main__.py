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
from .models import Release, ReleasePair

from . import __version__, initializeLogging, setCacheDirectory
from .env import env, getPipeline


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
@click.option("-c", "--cache", type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=pathlib.Path), default="cache", help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 5), help="Increase verbosity.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
@click.option("-p", "--provider", type=click.Choice(["default", "pidiff", "pycompat"]), default="default", help="Provider to use.")
@click.option("--pipeline", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-pipeline.yml", help="Pipeline file.", envvar="AEXPY_PIPELINE")
@click.option("--config", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-config.yml", help="Config file.", envvar="AEXPY_CONFIG")
def main(ctx=None, cache: pathlib.Path = "cache", verbose: int = 0, interact: bool = False, redo: bool = False, no_cache: bool = False, provider: "str" = "default", pipeline: pathlib.Path = "aexpy-pipeline.yml", config: pathlib.Path = "aexpy-config.yml") -> None:
    """Aexpy (https://github.com/StardustDL/aexpy)"""

    if isinstance(cache, str):
        cache = pathlib.Path(cache)
    if isinstance(pipeline, str):
        pipeline = pathlib.Path(pipeline)
    if isinstance(config, str):
        config = pathlib.Path(config)

    env.interact = interact
    if redo:
        env.redo = redo
    if no_cache:
        env.cached = not no_cache

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
                pass
            case "pidiff":
                from .third.pidiff.pipeline import getDefault
                env.provider = getDefault()
            case "pycompat":
                from .third.pycompat.pipeline import getDefault
                env.provider = getDefault()


@main.command()
@click.argument("project")
@click.argument("version")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def preprocess(project: str, version: str, redo: bool = False, no_cache: bool = False):
    """Preprocess a release."""
    release = Release(project, version)
    pipeline = getPipeline()
    result = pipeline.preprocess(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("project")
@click.argument("version")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def extract(project: str, version: str, redo: bool = False, no_cache: bool = False):
    """Extract the API in a release."""
    release = Release(project, version)
    pipeline = getPipeline()
    result = pipeline.extract(
        release, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def diff(project: str, old: str, new: str, redo: bool = False, no_cache: bool = False):
    """Diff two releases."""
    old = Release(project, old)
    new = Release(project, new)
    pipeline = getPipeline()
    result = pipeline.diff(old, new, redo=redo if redo else None,
                           cached=not no_cache if no_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def evaluate(project: str, old: str, new: str, redo: bool = False, no_cache: bool = False):
    """Evaluate differences between two releases."""
    old = Release(project, old)
    new = Release(project, new)
    pipeline = getPipeline()
    result = pipeline.eval(old, new, redo=redo if redo else None,
                           cached=not no_cache if no_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-C", "--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
def report(project: str, old: str, new: str, redo: bool = False, no_cache: bool = False) -> None:
    """Report breaking changes between two releases."""
    old = Release(project, old)
    new = Release(project, new)
    pipeline = getPipeline()
    result = pipeline.report(
        old, new, redo=redo if redo else None, cached=not no_cache if no_cache else None)
    assert result.success
    print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
def rebuild():
    """Rebuild the environment."""
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


@main.command()
@click.argument("items", default=None, nargs=-1)
@click.option("-s", "--stage", type=click.Choice(["pre", "ext", "dif", "eva", "rep", "ana", "all"]), default="all", help="Stage to run.")
@click.option("-f", "--file", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-batch.txt", help="File for items to process.")
@click.option("-w", "--worker", default=None, help="Number of workers.")
@click.option("-r", "--retry", default=5, help="Number of retries.")
def batch(items: "list[str] | None" = None, stage: "str" = "all", file: "pathlib.Path" = "aexpy-batch.txt", worker: "int | None" = None, retry: "int" = 5) -> None:
    """Run a batch of stages."""

    from .batch.processor import Processor
    from .batch import default

    if isinstance(file, str):
        file = pathlib.Path(file)

    items = list(items or [])

    toprocess: "list[ReleasePair]" = []

    if file.exists():
        rawitems = file.read_text().splitlines()
        items.extend(rawitems)

    for item in items:
        item = item.strip()
        if not item:
            continue
        try:
            pair = ReleasePair.fromId(item)
            toprocess.append(pair)
        except Exception as ex:
            print(f"Failed to parse item {item}: {ex})")

    hashset = set()
    singles: "list[Release]" = []

    for item in toprocess:
        id = str(item.old)
        if id not in hashset:
            singles.append(item.old)
            hashset.add(id)
        id = str(item.new)
        if id not in hashset:
            singles.append(item.new)
            hashset.add(id)

    with elapsedTimer() as elapsed:
        print(
            f"Running {stage} on {len(toprocess)} pairs, {len(singles)} releases @ {datetime.now()}.\n")
        match stage:
            case "pre":
                Processor(default.pre).process(
                    singles, workers=worker, retry=retry)
            case "ext":
                Processor(default.ext).process(
                    singles, workers=worker, retry=retry)
            case "dif":
                Processor(default.dif).process(
                    toprocess, workers=worker, retry=retry)
            case "eva":
                Processor(default.eva).process(
                    toprocess, workers=worker, retry=retry)
            case "rep":
                Processor(default.rep).process(
                    toprocess, workers=worker, retry=retry)
            case "ana":
                Processor(default.ext).process(
                    singles, workers=worker, retry=retry)
                Processor(default.dif).process(
                    toprocess, workers=worker, retry=retry)
                Processor(default.eva).process(
                    toprocess, workers=worker, retry=retry)
                Processor(default.rep).process(
                    toprocess, workers=worker, retry=retry)
            case "all":
                Processor(default.pre).process(
                    singles, workers=worker, retry=retry)
                Processor(default.ext).process(
                    singles, workers=worker, retry=retry)
                Processor(default.dif).process(
                    toprocess, workers=worker, retry=retry)
                Processor(default.eva).process(
                    toprocess, workers=worker, retry=retry)
                Processor(default.rep).process(
                    toprocess, workers=worker, retry=retry)
        print(
            f"\nFinished {stage} on {len(toprocess)} pairs, {len(singles)} releases in {timedelta(seconds=elapsed())} @ {datetime.now()}.")


@main.command()
@click.argument("projects", default=None, nargs=-1)
@click.option("-f", "--file", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-batch.txt", help="Output file.")
def generate(projects: "list[str] | None" = None, file: "pathlib.Path" = "aexpy-batch.txt"):
    """Generate batch pairs from projects."""

    from .batch.gen import pair, single

    projects = list(projects or [])

    if isinstance(file, str):
        file = pathlib.Path(file)

    items: "list[ReleasePair]" = []
    for project in projects:
        items.extend(pair(single(project)))

    file.write_text("\n".join((str(i) for i in items)))


@main.command()
@click.argument("projects", default=None, nargs=-1)
@click.option("-w", "--worker", type=int, default=None, help="Number of workers.")
@click.option("-r", "--retry", default=5, help="Number of retries.")
def process(projects: "list[str] | None" = None, worker: "int | None" = None, retry: "int" = 5):
    """Process projects."""

    from .batch.gen import single, pair, preprocessed, extracted, diffed, evaluated, reported
    from .batch.processor import Processor
    from .batch import default

    projects = list(projects or [])

    pipeline = getPipeline()

    count: "dict[str, int]" = {}

    for project in projects:
        with elapsedTimer() as elapsed:
            print(f"JOB: Processing {project} @ {datetime.now()}.")

            singles: "list[Release]" = single(project)
            count["preprocess"] = len(singles)
            print(
                f"JOB: Preprocess {project}: {len(singles)} releases @ {datetime.now()}.")
            Processor(default.pre).process(
                singles, workers=worker, retry=retry, stage="Preprocess")

            singles = list(filter(preprocessed(pipeline), singles))
            count["preprocessed"] = len(singles)
            count["extract"] = len(singles)
            print(f"JOB: Extract {project}: {len(singles)} releases.")
            Processor(default.ext).process(
                singles, workers=worker, retry=retry, stage="Extract")

            singles = list(filter(extracted(pipeline), singles))
            count["extracted"] = len(singles)
            pairs = pair(singles)
            count["diff"] = len(pairs)
            print(
                f"JOB: Diff {project}: {len(pairs)} pairs @ {datetime.now()}.")
            Processor(default.dif).process(
                pairs, workers=worker, retry=retry, stage="Diff")

            pairs = list(filter(diffed(pipeline), pairs))
            count["diffed"] = len(pairs)
            count["evaluate"] = len(pairs)
            print(
                f"JOB: Evaluate {project}: {len(pairs)} pairs @ {datetime.now()}.")
            Processor(default.eva).process(
                pairs, workers=worker, retry=retry, stage="Evaluate")

            pairs = list(filter(evaluated(pipeline), pairs))
            count["evaluated"] = len(pairs)
            count["report"] = len(pairs)
            print(
                f"JOB: Report {project}: {len(pairs)} pairs @ {datetime.now()}.")
            Processor(default.rep).process(
                pairs, workers=worker, retry=retry, stage="Report")

            pairs = list(filter(reported(pipeline), pairs))
            count["reported"] = len(pairs)
            print(
                f"JOB: Finish {project}: {len(pairs)} pairs @ {datetime.now()}.")

            print(
                f"JOB: Summary {project} ({timedelta(seconds=elapsed())}) @ {datetime.now()}: {', '.join((f'{k}: {v}' for k,v in count.items()))}.")


if __name__ == '__main__':
    main()
