import sys
from typing import IO
import click
from pathlib import Path
from aexpy.__main__ import exitWithContext

from aexpy.io import StreamProductSaver
from ...producers import produce
from . import StatisticianWorker, StatSummary


@click.command()
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path
    ),
)
@click.argument("output", type=click.File("wb"))
def main(files: list[Path], output: IO[bytes]):
    with produce(StatSummary()) as context:
        with context.using(StatisticianWorker()) as worker:
            worker.count(files, context.product)

    result = context.product
    StreamProductSaver(output).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    # if FLAG_interact:
    #     code.interact(banner="", local=locals())

    exitWithContext(context=context)


if __name__ == "__main__":
    main()
