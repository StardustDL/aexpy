import code
import sys
from pathlib import Path
from typing import IO

import click

from ...cli import CliContext, StreamProductSaver, exitWithContext
from ...producers import produce
from . import StatisticianWorker, StatSummary


@click.command()
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
    StreamProductSaver(output, gzip=clictx.compress).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)
