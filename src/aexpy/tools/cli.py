import code
import sys
from pathlib import Path
from typing import IO

import click

from ..cli import AliasedGroup, CliContext, StreamProductSaver, exitWithContext
from ..producers import produce
from .models import StatSummary
from .stats import StatisticianWorker


@click.group(cls=AliasedGroup)
@click.pass_context
def tool(
    ctx: click.Context,
) -> None:
    """Advanced tools

    The command name 'tool' can be omitted, directly using the name of subcommands."""
    pass


@tool.command()
@click.pass_context
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path
    ),
)
@click.argument("output", type=click.File("wb"))
def stat(ctx: click.Context, files: tuple[Path], output: IO[bytes]):
    """Count from produced data.

    FILES give paths to produced data for count.

    OUTPUT describes the output statistic file (in json format, use `-` for stdout).

    Examples:

    aexpy tool stat data/*.json stats.json
    """
    clictx = ctx.ensure_object(CliContext)

    with produce(StatSummary(), service=clictx.service.name) as context:
        with context.using(StatisticianWorker(logger=context.logger)) as worker:
            worker.count(files, context.product)

    result = context.product
    StreamProductSaver(output, gzip=clictx.gzip).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@tool.command()
@click.pass_context
@click.option(
    "-v",
    "--volume",
    type=click.Path(
        exists=True, dir_okay=True, file_okay=False, resolve_path=True, path_type=Path
    ),
    default=Path("."),
)
@click.option(
    "-t",
    "--tag",
    default="",
    help="Image tag, empty to use the same version as current.",
)
@click.argument(
    "args",
    nargs=-1,
)
def runimage(
    ctx: click.Context, args: tuple[str], volume: Path = Path("."), tag: str = ""
):
    """Quick runner to execute commands using AexPy images.

    VOLUME describes the mount directory for containers (to /data), default using current working directory.

    All file path arguments passed to container should use absolute paths with `/data` prefix or use a path relative to `/data`.

    Examples:

    aexpy tool runimage -v ./mount -- --version

    aexpy runimage -v ./mount -- extract ./dist.json ./api.json

    aexpy runimage -v ./mount -- extract /data/dist.json /data/api.json
    """
    clictx = ctx.ensure_object(CliContext)

    from .workers import AexPyDockerWorker

    worker = AexPyDockerWorker(
        cwd=volume, verbose=clictx.verbose, compress=clictx.gzip, tag=tag
    )

    result = worker.run(list(args), capture_output=False)

    exit(result.returncode)
