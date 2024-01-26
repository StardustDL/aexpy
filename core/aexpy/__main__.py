import code
import logging
import pathlib
from pathlib import Path
import sys
from typing import IO

import click

from aexpy.models import ProduceMode, ProduceState
from aexpy.caching import (
    FileProduceCache,
    StreamReaderProduceCache,
    StreamWriterProduceCache,
)
from aexpy.services import ServiceProvider

from . import __version__, initializeLogging
from . import json
from .models import ApiDescription, ApiDifference, Distribution, Release, ReleasePair, Report


FLAG_interact = False

services = ServiceProvider()


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
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


@click.group(cls=AliasedGroup)
@click.pass_context
@click.version_option(
    __version__,
    package_name="aexpy",
    prog_name="aexpy",
    message="%(prog)s v%(version)s.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    type=click.IntRange(0, 5),
    help="Increase verbosity.",
)
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
def main(ctx=None, verbose: int = 0, interact: bool = False) -> None:
    """
    AexPy /eɪkspaɪ/ is Api EXplorer in PYthon for detecting API breaking changes in Python packages. (ISSRE'22)

    Home page: https://aexpy.netlify.app/

    Repository: https://github.com/StardustDL/aexpy
    """
    global FLAG_interact
    FLAG_interact = interact

    loggingLevel = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.NOTSET,
    }[verbose]

    initializeLogging(loggingLevel)


@main.command()
@click.argument("distribution", type=click.File("w"))
@click.option(
    "-p", "--path",
    type=click.Path(
        exists=True,
        file_okay=False,
        resolve_path=True,
        dir_okay=True,
        path_type=Path,
    ),
    required=False,
)
@click.option("-m", "--module", multiple=True)
@click.option(
    "-r",
    "--release",
    default="unknown@unknown",
    help="Tag the release (project@version).",
)
def preprocess(
    distribution: IO[str],
    path: Path | None = None,
    module: list[str] | None = None,
    release: str = ""
):
    """Generate a release definition."""
    product = Distribution(release=Release.fromId(release))
    with product.produce(StreamWriterProduceCache(distribution), ProduceMode.Write) as product:
        product.pyversion = "3.11"
        product.rootPath = path
        product.topModules = list(module or [])
        product.producer = "aexpy"

    result = product
    print(result.overview(), file=sys.stderr)
    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


@main.command()
@click.argument("distribution", type=click.File("r"))
@click.argument("description", type=click.File("w"))
def extract(distribution: IO[str], description: IO[str]):
    """Extract the API in a distribution."""
    
    product = Distribution.fromCache(StreamReaderProduceCache(distribution))

    from .environments import CurrentEnvironment
    env = CurrentEnvironment

    result = services.extract(
        StreamWriterProduceCache(description), product, ProduceMode.Write, env=env
    )
    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


@main.command()
@click.argument("old", type=click.File("r"))
@click.argument("new", type=click.File("r"))
@click.argument("difference", type=click.File("w"))
def diff(old: IO[str], new: IO[str], difference: IO[str]):
    """Diff two releases."""
    oldData = ApiDescription.fromCache(StreamReaderProduceCache(old))
    newData = ApiDescription.fromCache(StreamReaderProduceCache(new))

    result = services.diff(
        StreamWriterProduceCache(difference), oldData, newData, ProduceMode.Write
    )
    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


@main.command()
@click.argument("difference", type=click.File("r"))
@click.argument("report", type=click.File("w"))
def report(difference: IO[str], report: IO[str]):
    """Report breaking changes between two releases."""

    data = ApiDifference.fromCache(StreamReaderProduceCache(difference))

    result = services.report(StreamWriterProduceCache(report), data, ProduceMode.Write)
    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."



@main.command()
@click.argument("data", type=click.File("r"))
def view(data: IO[str]):
    """View produced data."""
    cache = StreamReaderProduceCache(data)
    
    raw = json.loads(cache.data())

    cls = None
    if "release" in raw:
        cls = Distribution
    elif "distribution" in raw:
        cls = ApiDescription
    elif "entries" in raw:
        cls = ApiDifference
    else:
        cls = Report
    
    try:
        result = cls()
        result.load(raw)
    except Exception as ex:
        assert False, f"Failed to load data: {ex}"

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


if __name__ == "__main__":
    main()
