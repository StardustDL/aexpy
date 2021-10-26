import json
import logging
import pathlib
import time

import click
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

from aexpy import downloads
from aexpy.downloads.releases import DownloadInfo

from . import __version__
from .cli.analyze import analyze, cg
from .cli.diff import diff
from .cli.release import download, index, release
from .env import env


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("-D", "--directory", type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path), default=".", help="Path to working directory.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 4))
@click.option("--version", is_flag=True, default=False, help="Show the version.")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo mode.")
def main(ctx=None, directory: pathlib.Path = ".", verbose: int = 0, version: bool = False, interact: bool = False, redo: bool = False) -> None:
    """Aexpy (https://github.com/StardustDL/aexpy)"""

    logger = logging.getLogger("Cli-Main")

    loggingLevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
        4: logging.NOTSET
    }[verbose]

    logging.basicConfig(level=loggingLevel)

    logger.debug(f"Logging level: {loggingLevel}")

    env.setPath(directory)
    env.interactive = interact
    env.redo = redo

    logger.info(f"Working directory: {click.format_filename(env.path)}")

    if version:
        click.echo(f"Aexpy v{__version__}")
        exit(0)


main.add_command(index)
main.add_command(release)
main.add_command(download)
main.add_command(analyze)
main.add_command(cg)
main.add_command(diff)

if __name__ == '__main__':
    main()
