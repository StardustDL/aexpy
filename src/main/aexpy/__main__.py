import json
import logging
import pathlib
import time
from typing import Iterable, List, Optional

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
            downloaded = wheels.downloadWheel(
                releases.getDownloadInfo(rels[version]))
            print(f"Download to: {downloaded}")
            if unpack:
                unpacked = wheels.unpackWheel(downloaded)
                print(f"Unpack to: {unpacked}")
                print(wheels.getDistInfo(unpacked))
    else:
        result = releases.getReleases(project)
        print(json.dumps(result, indent=4))


def view(items: Iterable):
    for item in items:
        print(item)


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo.")
def analyze(project: str, version: str, interact: bool = False, redo: bool = False) -> None:
    from .downloads import releases, wheels
    from .analyses import serializer
    from .analyses.environment import analyze

    rels = releases.getReleases(project)
    downloadInfo = releases.getDownloadInfo(rels[version])
    if downloadInfo is None:
        raise ClickException("No this release")

    downloaded = wheels.downloadWheel(downloadInfo)
    api = analyze(downloaded, redo)
    if interact:
        import code
        code.interact(local={
            "api": api,
            "A": api,
            "manifest": api.manifest,
            "entries": api.entries,
            "names": api.names,
            "N": api.names,
            "E": api.entries,
            "EL": list(api.entries.values()),
            "M": api.modules,
            "ML": list(api.modules.values()),
            "C": api.classes,
            "CL": list(api.classes.values()),
            "F": api.funcs,
            "FL": list(api.funcs.values()),
            "P": api.fields,
            "PL": list(api.fields.values()),
            "view": view,
            "serializer": serializer,
        }, banner="Use api variable.")
    else:
        print(serializer.serialize(api, indent=4))



@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact.")
def cg(project: str, version: str, interact: bool = False) -> None:
    from .downloads import releases, wheels
    from .analyses import serializer
    from .analyses.environment import analyze
    from .analyses.enriching import callgraph

    rels = releases.getReleases(project)
    downloadInfo = releases.getDownloadInfo(rels[version])
    if downloadInfo is None:
        raise ClickException("No this release")

    downloaded = wheels.downloadWheel(downloadInfo)
    api = analyze(downloaded)
    cg = callgraph.build(api)
    if interact:
        import code
        code.interact(local={
            "api": api,
            "cg": cg,
        }, banner="Use cg variable.")
    else:
        print(cg)



@click.command()
@click.argument("project")
@click.argument("old")
@click.argument("new")
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact.")
@click.option("-r", "--redo", is_flag=True, default=False, help="Redo.")
def diff(project: str, old: str, new: str, interact: bool = False, redo: bool = False) -> None:
    from .downloads import releases, wheels
    from .analyses.environment import analyze
    from .diffs import serializer
    from .diffs.differ import diff

    rels = releases.getReleases(project)
    oldDownloadInfo = releases.getDownloadInfo(rels[old])
    newDownloadInfo = releases.getDownloadInfo(rels[new])
    if oldDownloadInfo is None or newDownloadInfo is None:
        raise ClickException("No this release")

    oldDownloaded = wheels.downloadWheel(oldDownloadInfo)
    newDownloaded = wheels.downloadWheel(newDownloadInfo)
    oldApi = analyze(oldDownloaded, redo)
    newApi = analyze(newDownloaded, redo)
    result = diff(oldApi, newApi, redo)
    if interact:
        import code
        code.interact(local={
            "diff": result,
            "D": result,
            "O": result.old,
            "N": result.new,
            "entries": result.entries,
            "E": result.entries,
            "EL": list(result.entries.values()),
            "kind": result.kind,
            "view": view,
            "serializer": serializer,
        }, banner="Use diff variable.")
    else:
        print(serializer.serialize(result, indent=4))


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
main.add_command(cg)
main.add_command(diff)

if __name__ == '__main__':
    main()
