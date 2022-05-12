import code
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

from aexpy import json
from aexpy.producer import ProducerOptions
from aexpy.utils import elapsedTimer

from . import __version__, initializeLogging, setCacheDirectory
from .env import Configuration, PipelineConfig, env, getPipeline
from .models import Release, ReleasePair


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
@click.version_option(__version__, package_name="aexpy", prog_name="aexpy", message="%(prog)s v%(version)s.")
@click.option("-c", "--cache", type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=pathlib.Path), default=None, help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 5), help="Increase verbosity.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
@click.option("-p", "--provider", default="", help="Provider to use.")
@click.option("--config", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-config.yml", help="Config file.", envvar="AEXPY_CONFIG")
def main(ctx=None, cache: "pathlib.Path | None" = None, verbose: int = 0, interact: bool = False, redo: bool = False, only_cache: "bool" = False, no_cache: bool = False, provider: "str" = "", config: pathlib.Path = "aexpy-config.yml") -> None:
    """
    AexPy

    AexPy /eɪkspaɪ/ is an Api EXplorer in PYthon.
    """

    if isinstance(cache, str):
        cache = pathlib.Path(cache)
    if isinstance(config, str):
        config = pathlib.Path(config)

    if config.exists() and config.is_file():
        try:
            data = yaml.safe_load(config.read_text())
            env.reset(Configuration.load(data))
        except Exception as ex:
            raise BadOptionUsage(f"Invalid config file: {config}") from ex

    env.interact = interact
    env.verbose = verbose

    if provider:
        env.provider = provider

    if cache:
        env.cache = cache

    env.prepare()

    logger = logging.getLogger("Cli-Main")

    if redo:
        env.options.redo = redo
    if no_cache:
        env.options.nocache = no_cache
    if only_cache:
        env.options.onlyCache = only_cache


@main.command()
@click.argument("release")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def preprocess(release: str, redo: bool = False, no_cache: bool = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Preprocess a release, project@version ."""
    release = Release.fromId(release)
    pipeline = getPipeline()
    result = pipeline.preprocess(
        release, options=ProducerOptions(redo=redo if redo else None, nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
    assert result.success

    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("release")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def extract(release: "str", redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Extract the API in a release, project@version ."""
    release = Release.fromId(release)
    pipeline = getPipeline()
    result = pipeline.extract(
        release, options=ProducerOptions(redo=redo if redo else None, nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
    assert result.success
    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def differ(pair: "str", redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Differ two releases, project@version1:version2 or project1@version1:project2@version2 ."""
    pair = ReleasePair.fromId(pair)
    pipeline = getPipeline()
    result = pipeline.diff(pair, options=ProducerOptions(redo=redo if redo else None,
                           nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
    assert result.success
    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def evaluate(pair: "str", redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Evaluate differences between two releases, project@version1:version2 or project1@version1:project2@version2 ."""
    pair = ReleasePair.fromId(pair)
    pipeline = getPipeline()
    result = pipeline.eval(pair, options=ProducerOptions(redo=redo if redo else None,
                           nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
    assert result.success
    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-C", "--only-cache", is_flag=True, help="Only load from cache.")
@click.option("--no-cache", is_flag=True, help="Disable caching.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo this step.")
@click.option("-R", "--reall", is_flag=True, default=False, help="Redo diff, eval and report.")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def report(pair: "str", redo: "bool" = False, no_cache: "bool" = False, reall: "bool" = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Report breaking changes between two releases, project@version1:version2 or project1@version1:project2@version2 ."""
    pair = ReleasePair.fromId(pair)
    pipeline = getPipeline()

    if reall:
        redo = True
        result = pipeline.diff(pair, options=ProducerOptions(redo=redo if redo else None,
                               nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
        assert result.success
        result = pipeline.eval(pair, options=ProducerOptions(redo=redo if redo else None,
                               nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
        assert result.success

    result = pipeline.report(pair, options=ProducerOptions(redo=redo if redo else None,
                             nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))
    assert result.success
    if result.file:
        print(result.file.read_text())

    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
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
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def batch(project: "str", workers: "int | None" = None, retry: "int" = 3, redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Process project."""
    pipeline = getPipeline()

    result = pipeline.batch(
        project, workers, retry, options=ProducerOptions(redo=redo if redo else None, nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))

    assert result.success
    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
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
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def index(project: "str", workers: "int | None" = None, retry: "int" = 3, redo: "bool" = False, no_cache: "bool" = False, only_cache: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Process project."""
    pipeline = getPipeline()
    result = pipeline.index(
        project, workers, retry, options=ProducerOptions(redo=redo if redo else None, nocache=no_cache if no_cache else None, onlyCache=only_cache if only_cache else None))

    assert result.success
    if log:
        print(result.logFile.read_text())
    elif json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.option("-c", "--clear", is_flag=True, help="Clear the created environment.")
def prepare(clear: "bool" = False):
    """Rebuild the environment."""
    if clear:
        from aexpy.environments.conda import CondaEnvironment
        CondaEnvironment.clearEnv()

        from aexpy.extracting.environments.default import DefaultEnvironment
        DefaultEnvironment.clearEnv()

        from aexpy.third.pycompat.extractor import PycompatEnvironment
        PycompatEnvironment.clearEnv()

        from aexpy.extracting.third.pycg import PycgEnvironment
        PycgEnvironment.clearEnv()

        return

    from aexpy.environments.conda import CondaEnvironment
    CondaEnvironment.clearBase()
    CondaEnvironment.buildAllBase()

    from aexpy.extracting.environments.default import DefaultEnvironment
    DefaultEnvironment.clearBase()
    DefaultEnvironment.buildAllBase()

    if os.getenv("THIRD_PARTY"):

        from aexpy.third.pycompat.extractor import PycompatEnvironment
        PycompatEnvironment.clearBase()
        PycompatEnvironment.buildAllBase()

        from aexpy.extracting.third.pycg import PycgEnvironment
        PycgEnvironment.clearBase()
        PycgEnvironment.buildAllBase()

        if not os.getenv("RUN_IN_DOCKER"):
            from aexpy.third.pidiff.evaluator import Evaluator
            Evaluator.clearBase()
            Evaluator.buildAllBase()


@main.command()
@click.option("-d", "--debug", is_flag=True, help="Debug mode.")
@click.option("-p", "--port", type=int, default=8008, help="Port to listen on.")
@click.option("-u", "--user", default="", help="Auth user to protect the website (Basic Auth), empty for public access.")
@click.option("-P", "--password", default="", help="Auth password to protect the website (Basic Auth), empty for public access.")
def serve(debug: "bool" = False, port: "int" = 8008, user: "str" = "", password: "str" = ""):
    from .serving.server.entrypoint import serve as inner
    inner(debug, port, user, password)


if __name__ == '__main__':
    main()
