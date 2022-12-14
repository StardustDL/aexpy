import code
import logging
import os
import pathlib

import click
import yaml
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

from aexpy.models import ProduceMode

from . import __version__
from .env import Configuration, env, getPipeline
from .models import BatchRequest, Release, ReleasePair


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
        assert cmd is not None, "Command is None."
        return cmd.name, cmd, args


def parseMode(mode: "str"):
    return {
        "r": ProduceMode.Read,
        "w": ProduceMode.Write
    }.get(mode, ProduceMode.Access)


@click.group(cls=AliasedGroup)
@click.pass_context
@click.version_option(__version__, package_name="aexpy", prog_name="aexpy", message="%(prog)s v%(version)s.")
@click.option("-c", "--cache", type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=pathlib.Path), default=None, help="Path to cache directory.", envvar="AEXPY_CACHE")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 5), help="Increase verbosity.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-p", "--pipeline", default="", help="Pipeline to use.")
@click.option("--config", type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default="aexpy-config.yml", help="Config file.", envvar="AEXPY_CONFIG")
def main(ctx=None, cache: "pathlib.Path | None" = None, verbose: int = 0, interact: bool = False, pipeline: "str" = "", config: pathlib.Path = pathlib.Path("aexpy-config.yml")) -> None:
    """
    AexPy /e??kspa??/ is Api EXplorer in PYthon for detecting API breaking changes in Python packages. (ISSRE'22)

    Home page: https://aexpy.netlify.app/

    Repository: https://github.com/StardustDL/aexpy
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
            raise BadOptionUsage(
                "config", f"Invalid config file: {config}") from ex

    env.interact = interact
    env.verbose = verbose

    if pipeline:
        env.pipeline = pipeline

    if cache:
        env.cache = cache

    env.prepare()

    logger = logging.getLogger("Cli-Main")


@main.command()
@click.argument("release")
@click.option("-m", "--mode", type=click.Choice(["a", "r", "w"], case_sensitive=False), default="a", help="Produce mode (Access / Read / Write).")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def preprocess(release: str, mode: "str" = "a", json: "bool" = False, log: "bool" = False):
    """Preprocess a release.

    project@version"""
    releaseVal = Release.fromId(release)
    pipeline = getPipeline()

    if log:
        print(env.services.logPreprocess(pipeline.preprocessor, releaseVal))
        return

    result = pipeline.preprocess(releaseVal, parseMode(mode))
    assert result.success

    if json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("release")
@click.option("-m", "--mode", type=click.Choice(["a", "r", "w"], case_sensitive=False), default="a", help="Produce mode (Access / Read / Write).")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def extract(release: "str", mode: "str" = "a", json: "bool" = False, log: "bool" = False):
    """Extract the API in a release.

    project@version"""
    releaseVal = Release.fromId(release)
    pipeline = getPipeline()

    if log:
        print(env.services.logExtract(pipeline.extractor, releaseVal))
        return

    result = pipeline.extract(releaseVal, parseMode(mode))
    assert result.success
    if json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-m", "--mode", type=click.Choice(["a", "r", "w"], case_sensitive=False), default="a", help="Produce mode (Access / Read / Write).")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def diff(pair: "str", mode: "str" = "a", json: "bool" = False, log: "bool" = False):
    """Diff two releases.

    project@version1:version2 or project1@version1:project2@version2.
    """
    pairVal = ReleasePair.fromId(pair)
    pipeline = getPipeline()

    if log:
        print(env.services.logDiff(pipeline.differ, pairVal))
        return

    result = pipeline.diff(pairVal, parseMode(mode))
    assert result.success
    if json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("pair")
@click.option("-m", "--mode", type=click.Choice(["a", "r", "w"], case_sensitive=False), default="a", help="Produce mode (Access / Read / Write).")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def report(pair: "str", mode: "str" = "a", json: "bool" = False, log: "bool" = False):
    """Report breaking changes between two releases.

    project@version1:version2 or project1@version1:project2@version2
    """
    pairVal = ReleasePair.fromId(pair)
    pipeline = getPipeline()

    if log:
        print(env.services.logReport(pipeline.reporter, pairVal))
        return

    result = pipeline.report(pairVal, parseMode(mode))
    assert result.success
    if result.content:
        print(result.content)

    if json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.argument("project")
@click.option("-m", "--mode", type=click.Choice(["a", "r", "w"], case_sensitive=False), default="a", help="Produce mode (Access / Read / Write).")
@click.option("-w", "--workers", type=int, default=None, help="Number of workers.")
@click.option("-t", "--retry", default=3, help="Number of retries.")
@click.option("-i", "--index", is_flag=True, help="Only index results.")
@click.option("--json", is_flag=True, help="Output as JSON.")
@click.option("--log", is_flag=True, help="Output log.")
def batch(project: "str", workers: "int | None" = None, retry: "int" = 3, mode: "str" = "a", index: "bool" = False, json: "bool" = False, log: "bool" = False):
    """Process project."""
    pipeline = getPipeline()

    request = BatchRequest(pipeline=pipeline.name, project=project,
                           workers=workers, retry=retry, index=index)

    if log:
        print(env.services.logBatch(pipeline.batcher, request))
        return

    result = pipeline.batch(request, parseMode(mode))

    assert result.success
    if json:
        print(result.dumps())
    else:
        print(result.overview())

    if env.interact:
        code.interact(banner="", local=locals())


@main.command()
@click.option("-c", "--clear", is_flag=True, help="Clear the created environment.")
def initialize(clear: "bool" = False):
    """Rebuild the environment."""
    if clear:
        from aexpy.environments.conda import CondaEnvironment
        CondaEnvironment.clearEnv()

        from aexpy.extracting.environments.default import DefaultEnvironment
        DefaultEnvironment.clearEnv()

        if os.getenv("THIRD_PARTY"):
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
            from aexpy.third.pidiff.differ import Evaluator
            Evaluator.clearBase()
            Evaluator.buildAllBase()


@main.command()
@click.option("-d", "--debug", is_flag=True, help="Debug mode.")
@click.option("-p", "--port", type=int, default=8008, help="Port to listen on.")
@click.option("-u", "--user", default="", help="Auth user to protect the website (Basic Auth), empty for public access.")
@click.option("-P", "--password", default="", help="Auth password to protect the website (Basic Auth), empty for public access.")
def serve(debug: "bool" = False, port: "int" = 8008, user: "str" = "", password: "str" = ""):
    """Serve web server."""
    from .serving.server.entrypoint import serve as inner
    inner(debug, port, user, password)


if __name__ == '__main__':
    main()
