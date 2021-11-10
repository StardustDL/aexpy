import pathlib
from dataclasses import asdict

import click
from click import ClickException

from aexpy.analyses.__main__ import import_module
from aexpy.analyses.models import ApiEntry, AttributeEntry, ClassEntry, CollectionEntry, FunctionEntry, ModuleEntry, SpecialEntry

from ..env import env
from . import interactive


def readEntry(entries: ApiEntry | list[ApiEntry]):
    if isinstance(entries, ApiEntry):
        entries = [entries]
    for entry in entries:
        match entry:
            case ModuleEntry() as module:
                print("Module", end=" ")
            case ClassEntry() as cls:
                print("Class", end=" ")
            case FunctionEntry() as func:
                print("Function", end=" ")
            case AttributeEntry() as attr:
                print("Attribute", end=" ")
            case SpecialEntry() as spe:
                print("Special", end=" ")
        print(f"{entry.name}({entry.id}) @ {entry.location}")
        if isinstance(entry, CollectionEntry):
            print("  Members:")
            for member, target in entry.members.items():
                print(f"    {member} -> {target}")
            print(f"  Annotations: {entry.annotations}")
        match entry:
            case ModuleEntry() as module:
                pass
            case ClassEntry() as cls:
                print(f"  Bases: {cls.bases}")
                print(f"  Mro: {cls.mro}")
            case FunctionEntry() as func:
                print(f"  Bound: {func.bound}")
                print("  Parameters:")
                for para in entry.parameters:
                    print(f"    {para}")
                print(f"  Return: {func.returnType}({func.returnAnnotation})")
                print(f"  Annotations: {func.annotations}")
            case AttributeEntry() as attr:
                print(f"  Bound: {attr.bound}")
                print(f"  Type: {attr.type}")
            case SpecialEntry() as spe:
                print(f"  Kind: {spe.kind}")
                print(f"  Data: {spe.data}")
        print("")


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

            def scopedRead(args):
                if isinstance(args, str):
                    readEntry(api.entries[args])
                else:
                    readEntry(args)
            
            def inputHook(prompt):
                raw = input(prompt)
                if raw in api.entries:
                    return f"read('{raw}')"
                return raw

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
                "PL": list(api.attrs.values()),
                "read": scopedRead
            }, readhook=inputHook)
        else:
            click.echo(serializer.serialize(api, indent=4))
    else:
        click.echo("Failed to analyze.")
        accessLog(downloaded)
