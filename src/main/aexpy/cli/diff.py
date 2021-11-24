import click
from click import ClickException
from aexpy.analyses.models import ApiEntry

from aexpy.diffs.models import DiffEntry

from ..env import env
from . import interactive


@click.command()
@click.argument("project")
@click.argument("old", default="")
@click.argument("new", default="")
@click.option("-a", "--all", is_flag=True, default=False, help="All version.")
def diff(project: str, old: str = "", new: str = "", all: bool = False) -> None:
    """Compare API."""
    if all:
        from ..jobs import diffs

        diffs.diffProject(project)
    else:
        if not old or not new:
            raise ClickException("Please specify old and new version.")
        from ..analyses.environment import analyze
        from ..analyses.environment import getLog as analyzeLog
        from ..diffs import serializer
        from ..diffs.environment import diff
        from ..downloads import releases, wheels
        from ..jobs import diffs
        from .analyze import readEntry as readApiEntry

        rels = releases.getReleases(project)
        oldDownloadInfo = releases.getDownloadInfo(rels[old])
        newDownloadInfo = releases.getDownloadInfo(rels[new])
        if oldDownloadInfo is None or newDownloadInfo is None:
            raise ClickException("No this release")

        oldDownloaded = wheels.downloadWheel(oldDownloadInfo)
        newDownloaded = wheels.downloadWheel(newDownloadInfo)
        oldApi = analyze(oldDownloaded)
        if oldApi is None:
            raise ClickException(f"Failed to analyze {project} @ {old}.")
        oldLog = analyzeLog(oldDownloaded)
        newApi = analyze(newDownloaded)
        if newApi is None:
            raise ClickException(f"Failed to analyze {project} @ {new}.")
        newLog = analyzeLog(newDownloaded)
        result = diff(oldApi, newApi)
        if env.interactive:
            def scopedRead(args):
                if isinstance(args, str):
                    readEntry(result.entries[args])
                elif isinstance(args, ApiEntry):
                    readApiEntry(args)
                else:
                    readEntry(args)

            def inputHook(prompt):
                raw = input(prompt)
                if raw in result.entries:
                    return f"read('{raw}')"

                return raw

            interactive.interact({
                "diff": result,
                "O": oldApi,
                "N": newApi,
                "OL": oldLog,
                "NL": newLog,
                "D": result,
                "OM": result.old,
                "NM": result.new,
                "entries": result.entries,
                "E": result.entries,
                "EL": list(result.entries.values()),
                "kind": result.kind,
                "kinds": result.kinds(),
                "read": scopedRead,
                "readapi": readApiEntry,
            }, readhook=inputHook)
        else:
            click.echo(serializer.serialize(result, indent=4))
