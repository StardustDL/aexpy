import pathlib
from dataclasses import asdict

import click
from click import ClickException
from mypy.types import Type

from aexpy.analyses.__main__ import import_module
from aexpy.analyses.models import ApiCollection, ApiEntry, AttributeEntry, ClassEntry, CollectionEntry, FunctionEntry, ModuleEntry, SpecialEntry
from aexpy.diffs.models import DiffCollection, DiffEntry
from aexpy.logging.models import PayloadLog
from aexpy.analyses.enriching.types import decodeType

from ..env import env
from . import interactive


def readType(typeStr: str | FunctionEntry | AttributeEntry) -> Type:
    if isinstance(typeStr, ApiEntry):
        typeStr = typeStr.type
    return decodeType(typeStr).text


def readApiEntry(entries: ApiEntry | list[ApiEntry]):
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
                print(f"  Type: {func.type}")
                print("  Parameters:")
                for para in entry.parameters:
                    print(
                        f"    {para.name} ({para.kind.name}, {'Optional' if para.optional else 'Required'})")
                    print(f"      Type: {para.type}")
                    if para.optional:
                        print(f"      Default: {para.default}")
                    print(f"      Annotation: {para.annotation}")
                print(
                    f"  Return: {func.returnType}({func.returnAnnotation})")
                print(f"  Annotations: {func.annotations}")
            case AttributeEntry() as attr:
                print(f"  Bound: {attr.bound}")
                print(f"  Type: {attr.type}({attr.rawType})")
            case SpecialEntry() as spe:
                print(f"  Kind: {spe.kind.name}")
                print(f"  Data: {spe.data}")
        print("")


def readDiffEntry(entries: DiffEntry | list[DiffEntry]):
    if isinstance(entries, DiffEntry):
        entries = [entries]
    for entry in entries:
        if not isinstance(entry, DiffEntry):
            continue
        print(f"{entry.id}")
        print(f"  {entry.kind}: {entry.message}")
        print(f"  Old: {entry.old}")
        print(f"  New: {entry.new}")
        print("")


def viewLog(data: PayloadLog, script: str | None = None):
    from ..logging.serializer import serialize

    execEnv = {
        "log": data,
        **asdict(data)
    }

    if script:
        exec(script, execEnv)
        return

    if env.interactive:
        interactive.interact(execEnv)
    else:
        click.echo(serialize(data, indent=4))


def viewLogFile(path: pathlib.Path, script: str | None = None):
    from ..logging.serializer import deserialize
    log = deserialize(path.read_text())
    viewLog(log, script)


def viewAnalysisResult(api: ApiCollection, log: PayloadLog | None, script: str | None = None):
    from ..analyses.serializer import serialize

    def scopedRead(args):
        if isinstance(args, str):
            readApiEntry(api.entries[args])
        else:
            readApiEntry(args)

    execEnv = {
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
        "read": scopedRead,
        "readtype": readType,
        "decodetype": decodeType,
    }

    if script:
        exec(script, execEnv)
        return

    if env.interactive:
        def inputHook(prompt):
            raw = input(prompt)
            if raw in api.entries:
                return f"read('{raw}')"
            return raw

        interactive.interact(execEnv, readhook=inputHook)
    else:
        click.echo(serialize(api, indent=4))


def viewAnalysisResultFile(path: pathlib.Path, script: str | None = None):
    from ..analyses.serializer import deserialize

    api = deserialize(path.read_text())

    from ..logging.serializer import deserialize as logDeserialize
    logPath = path.parent.joinpath(f"{path.stem}.log.json")
    log = logDeserialize(logPath.read_text()) if logPath.exists() else None
    viewAnalysisResult(api, log, script)


def viewDiffResult(result: DiffCollection, script: str | None = None):
    from ..diffs.serializer import serialize

    def scopedRead(args):
        if isinstance(args, str):
            readDiffEntry(result.entries[args])
        elif isinstance(args, ApiEntry):
            readApiEntry(args)
        else:
            readDiffEntry(args)

    execEnv = {
        "diff": result,
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
        "readtype": readType,
        "decodetype": decodeType,
    }

    if script:
        exec(script, execEnv)
        return

    if env.interactive:
        def inputHook(prompt):
            raw = input(prompt)
            if raw in result.entries:
                return f"read('{raw}')"

            return raw

        interactive.interact(execEnv, readhook=inputHook)
    else:
        click.echo(serialize(result, indent=4))


def viewDiffResultFile(path: pathlib.Path, script: str | None = None):
    from ..diffs.serializer import deserialize

    result = deserialize(path.read_text())
    viewDiffResult(result, script)


@click.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path))
@click.option("-s", "--script", type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=pathlib.Path), default=None, help="Path to the script.")
def view(file: pathlib.Path, script: pathlib.Path | None = None) -> None:
    scriptSrc = script.read_text() if script else None

    if scriptSrc is not None:
        lines = scriptSrc.splitlines()
        try:
            index = lines.index("# START")
        except:
            index = 0
        scriptSrc = "\n".join(lines[index:])

    if ".log" in file.suffixes:
        viewLogFile(file, scriptSrc)
    with file.open("r", encoding="utf-8") as f:
        if f.read(20).startswith('{"manifest":'):
            viewAnalysisResultFile(file, scriptSrc)
        else:
            viewDiffResultFile(file, scriptSrc)


@click.command()
@click.argument("file", type=click.Path(dir_okay=False, resolve_path=True, path_type=pathlib.Path))
@click.option("-s", "--schema", type=click.Choice(["a", "d", "l"]), default="a", help="Type for the view script")
def viewgen(file: pathlib.Path, schema: str = "a"):
    src = pathlib.Path(__file__).parent.joinpath("scripts")
    match schema:
        case "a":
            src = src.joinpath("analysis.py")
        case "d":
            src = src.joinpath("diff.py")
        case "l":
            src = src.joinpath("log.py")
    if file.exists():
        raise ClickException(f"File {file} has existed.")
    file.write_text(src.read_text())
