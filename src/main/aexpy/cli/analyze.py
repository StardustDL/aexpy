import click
from click import ClickException
from . import interactive
from ..env import env


@click.command()
@click.argument("project")
@click.argument("version")
def cg(project: str, version: str, interact: bool = False) -> None:
    """View callgraph."""
    from ..downloads import releases, wheels
    from ..analyses import serializer
    from ..analyses.environment import analyze
    from ..analyses.enriching import callgraph

    rels = releases.getReleases(project)
    downloadInfo = releases.getDownloadInfo(rels[version])
    if downloadInfo is None:
        raise ClickException("No this release")

    downloaded = wheels.downloadWheel(downloadInfo)
    api = analyze(downloaded)
    cg = callgraph.build(api)
    if interact:
        interactive.interact({
            "api": api,
            "cg": cg,
        })
    else:
        click.echo(str(cg))


@click.command()
@click.argument("project")
@click.argument("version", default="")
def analyze(project: str, version: str) -> None:
    """Analyze API."""
    from ..downloads import releases, wheels
    from ..analyses import serializer
    from ..analyses.environment import analyze

    rels = releases.getReleases(project)
    downloadInfo = releases.getDownloadInfo(rels[version])
    if downloadInfo is None:
        raise ClickException("No this release.")

    downloaded = wheels.downloadWheel(downloadInfo)
    api = analyze(downloaded)
    if env.interactive:
        interactive.interact({
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
            "PL": list(api.fields.values())
        })
    else:
        click.echo(serializer.serialize(api, indent=4))
