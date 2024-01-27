import code
import logging
import pathlib
from pathlib import Path
import sys
from typing import IO

import click

from aexpy.models import ProduceState
from aexpy.caching import (
    FileProduceCache,
    StreamReaderProduceCache,
    StreamWriterProduceCache,
)

from . import __version__, initializeLogging
from .models import ApiDescription, ApiDifference, Distribution, Release, ReleasePair, Report
from .producers import produce


FLAG_interact = False


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
    from .models import Distribution
    with produce(Distribution(release=Release.fromId(release))) as context:
        context.product.pyversion = "3.11"
        context.product.rootPath = path
        context.product.topModules = list(module or [])
        context.product.producer = "aexpy"

    result = context.product
    StreamWriterProduceCache(distribution).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


@main.command()
@click.argument("distribution", type=click.File("r"))
@click.argument("description", type=click.File("w"))
def extract(distribution: IO[str], description: IO[str]):
    """Extract the API in a distribution."""
    
    data = StreamReaderProduceCache(distribution).data(Distribution)
    with produce(ApiDescription(distribution=data)) as context:
        from .environments import CurrentEnvironment
        from .extracting.default import DefaultExtractor

        extractor = DefaultExtractor(env=CurrentEnvironment, logger=context.logger)
        context.use(extractor)
        extractor.extract(data, context.product)
        
    result = context.product
    StreamWriterProduceCache(description).save(result, context.log)

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
    oldData = StreamReaderProduceCache(old).data(ApiDescription)
    newData = StreamReaderProduceCache(new).data(ApiDescription)

    with produce(ApiDifference(old=oldData.distribution, new=newData.distribution)) as context:
        from .diffing.default import DefaultDiffer

        differ = DefaultDiffer(logger=context.logger)
        context.use(differ)
        differ.diff(oldData, newData, context.product)

    result = context.product
    StreamWriterProduceCache(difference).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


@main.command()
@click.argument("difference", type=click.File("r"))
@click.argument("report", type=click.File("w"))
def report(difference: IO[str], report: IO[str]):
    """Report breaking changes between two releases."""

    data = StreamReaderProduceCache(difference).data(ApiDifference)

    with produce(Report(old=data.old, new=data.new)) as context:
        from .reporting.text import TextReporter

        reporter = TextReporter(logger=context.logger)
        context.use(reporter)
        reporter.report(data, context.product)

    result = context.product
    StreamWriterProduceCache(report).save(result, context.log)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."



@main.command()
@click.argument("data", type=click.File("r"))
def view(data: IO[str]):
    """View produced data."""

    from pydantic import TypeAdapter
    cache = StreamReaderProduceCache(data)
    
    try:
        result = TypeAdapter(Distribution | ApiDescription | ApiDifference | Report).validate_json(cache.raw())
    except Exception as ex:
        assert False, f"Failed to load data: {ex}"

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    assert result.state == ProduceState.Success, "Failed to process."


if __name__ == "__main__":
    main()
