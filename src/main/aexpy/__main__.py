import json
import logging
import pathlib
import time
from typing import Optional

import click
from click import BadArgumentUsage, BadOptionUsage, BadParameter
from click.exceptions import ClickException

from aexpy import downloads

from . import __version__
from .env import env


@click.command()
def init() -> None:
    """Prepare working."""
    env.prepare()


@click.command()
def index() -> None:
    from .downloads import index
    data = index.getIndex()
    click.echo(data)
    click.echo(len(data))


@click.command()
@click.argument("project")
@click.option("-v", "--version", default="")
@click.option("-d", "--download", is_flag=True, default=False, help="Download.")
@click.option("-x", "--unpack", is_flag=True, default=False, help="Unpack.")
def release(project: str, version: str = "", download: bool = False, unpack: bool = False) -> None:
    from .downloads import releases, wheels
    download = download or unpack
    if version:
        result = releases.getReleaseInfo(project, version)
        print(json.dumps(result, indent=4))
        if result and download:
            rels = releases.getReleases(project)
            downloaded = wheels.downloadWheel(releases.getDownloadInfo(rels[version]))
            print(f"Download to: {downloaded}")
            if unpack:
                unpacked = wheels.unpackWheel(downloaded)
                print(f"Unpack to: {unpacked}")
                print(wheels.getDistInfo(unpacked))
    else:
        result = releases.getReleases(project)
        print(json.dumps(result, indent=4))


@click.command()
@click.argument("project")
@click.argument("version")
def analyze(project: str, version: str) -> None:
    from .downloads import releases, wheels
    from .analyses.environment import getAnalysisImage, runAnalysis

    releaseInfo = releases.getReleaseInfo(project, version)
    rels = releases.getReleases(project)
    downloaded = wheels.downloadWheel(releases.getDownloadInfo(rels[version]))
    unpacked = wheels.unpackWheel(downloaded)
    distinfo = wheels.getDistInfo(unpacked)
    pythonVersion = wheels.getAvailablePythonVersion(distinfo)

    image = getAnalysisImage(pythonVersion)
    print(runAnalysis(image, downloaded, unpacked, distinfo.topLevel))


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("-D", "--directory", type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path), default=".", help="Path to working directory.")
@click.option("-v", "--verbose", count=True, default=0, type=click.IntRange(0, 4))
@click.option("--version", is_flag=True, default=False, help="Show the version.")
def main(ctx=None, directory: pathlib.Path = ".", verbose: int = 0, version: bool = False) -> None:
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

    logger.info(f"Working directory: {click.format_filename(env.path)}")

    if version:
        click.echo(f"Aexpy v{__version__}")
        exit(0)


main.add_command(init)
main.add_command(index)
main.add_command(release)
main.add_command(analyze)

if __name__ == '__main__':
    main()
