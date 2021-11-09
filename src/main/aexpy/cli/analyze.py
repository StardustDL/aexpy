from dataclasses import asdict
import pathlib
import click
from click import ClickException

from aexpy.analyses.__main__ import import_module

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
    if env.interactive:
        interactive.interact({
            "log": log,
            **asdict(log)
        })
    else:
        click.echo(serialize(log, indent=4))


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
        if env.interactive:
            log = getLog(downloaded)
            interactive.interact({
                "api": api,
                "log": log,
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
                "P": api.attrs,
                "PL": list(api.attrs.values())
            })
        else:
            click.echo(serializer.serialize(api, indent=4))
    else:
        click.echo("Failed to analyze.")
        accessLog(downloaded)
