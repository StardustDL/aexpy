import code
import sys
from pathlib import Path
from typing import IO

import click

from ..cli import AliasedGroup, CliContext, StreamProductSaver, exitWithContext
from ..producers import produce
from .models import StatSummary


@click.group(cls=AliasedGroup)
@click.pass_context
def tool(
    ctx: click.Context,
) -> None:
    """Advanced tools."""
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
def stat(ctx: click.Context, files: list[Path], output: IO[bytes]):
    """Count from produced data."""
    clictx = ctx.ensure_object(CliContext)

    with produce(StatSummary(), service=clictx.service.name) as context:
        with context.using(
            clictx.service.statistician(logger=context.logger)
        ) as worker:
            worker.count(files, context.product)

    result = context.product
    StreamProductSaver(output, gzip=clictx.gzip).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)
