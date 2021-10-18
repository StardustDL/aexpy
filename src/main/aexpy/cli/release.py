import click
import json
from . import interactive
from ..env import env


@click.command()
def index() -> None:
    """View all package from index."""
    from ..downloads import index
    data = index.getIndex()
    if env.interactive:
        interactive.interact({
            "index": data
        })
    else:
        click.echo(json.dumps(data, indent=4))


@click.command()
@click.argument("project")
@click.argument("version", default="")
def release(project: str, version: str = "") -> None:
    """View release information."""
    from ..downloads import releases
    if version:
        result = releases.getReleaseInfo(project, version)
    else:
        result = releases.getReleases(project)
    if env.interactive:
        interactive.interact({
            "release": result
        })
    else:
        click.echo(json.dumps(result, indent=4))


@click.command()
@click.argument("project")
@click.argument("version", default="")
def download(project: str, version: str = "") -> None:
    """Download and extract wheel distributions."""
    from ..jobs import downloads
    if version:
        downloads.downloadVersion(project, version)
    else:
        downloads.downloadProject(project)
