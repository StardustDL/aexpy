import pathlib
from dataclasses import asdict

import click
from click import ClickException

from aexpy.analyses.__main__ import import_module
from aexpy.analyses.models import ApiEntry, AttributeEntry, ClassEntry, CollectionEntry, FunctionEntry, ModuleEntry, SpecialEntry
from aexpy.logging.models import PayloadLog

from ..env import env
from . import interactive


@click.command()
@click.argument("project")
@click.argument("version")
def cg(project: str, version: str, interact: bool = False) -> None:
    """View callgraph."""
    from ..analyses import serializer
    from ..analyses.enriching import callgraph
    from ..analyses.environment import analyze
    from ..downloads import releases, wheels

    rels = releases.getReleases(project)
    downloadInfo = releases.getDownloadInfo(rels[version])
    if downloadInfo is None:
        raise ClickException("No this release")

    downloaded = wheels.downloadWheel(downloadInfo)
    api = analyze(downloaded)
    if api is None:
        raise ClickException("Failed to analyze.")

    cg = callgraph.build(api)

    if interact:
        interactive.interact({
            "api": api,
            "cg": cg,
        })
    else:
        click.echo(str(cg))


def accessLog(wheelFile: pathlib.Path):
    from ..analyses.environment import getLog
    from ..logging.serializer import serialize
    log = getLog(wheelFile)
    if log is None:
        raise ClickException(f"No logs for {wheelFile}.")
    from .view import viewLog
    viewLog(log)


@click.command()
@click.argument("project")
@click.argument("version")
@click.option("-l", "--log", is_flag=True, default=False, help="Only access logs.")
def analyze(project: str, version: str, log: bool = False) -> None:
    """Analyze API."""
    from ..analyses import serializer
    from ..analyses.environment import analyze, getLog
    from ..downloads import releases, wheels

    rels = releases.getReleases(project)
    downloadInfo = releases.getDownloadInfo(rels[version])
    if downloadInfo is None:
        raise ClickException("No this release.")

    downloaded = wheels.downloadWheel(downloadInfo)

    if log:
        accessLog(downloaded)
        return

    api = analyze(downloaded)
    if api is not None:
        log = None
        if env.interactive:
            log = getLog(downloaded)
        from .view import viewAnalysisResult
        viewAnalysisResult(api, log)
    else:
        click.echo("Failed to analyze.")
        accessLog(downloaded)
