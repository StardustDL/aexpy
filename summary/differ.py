from aexpy.third.pycompat.pipeline import getDefault as getDefaultPycompat
from aexpy.third.pidiff.pipeline import getDefault as getDefaultPidiff
from dataclasses import dataclass, field, asdict
from json import load
from aexpy import json
from pathlib import Path

from aexpy import setCacheDirectory
from aexpy.batching.loaders import BatchLoader
from aexpy.env import PipelineConfig
from aexpy.models import ApiBreaking, Release, ReleasePair
from aexpy.models.difference import BreakingRank, DiffEntry
from aexpy.pipelines import Pipeline
from aexpy.utils import ensureDirectory
from . import defaultProjects, cacheRoot


@dataclass
class DiffSummary:
    project: str
    done: list[str] = field(default_factory=list)
    allpidiff: dict[str, int] = field(default_factory=dict)
    allpycompat: dict[str, int] = field(default_factory=dict)
    alldefault: dict[str, int] = field(default_factory=dict)
    uniques: dict[str, list[str]] = field(default_factory=dict)
    uniqueBcs: dict[str, list[str]] = field(default_factory=dict)
    cants: dict[str, list[str]] = field(default_factory=dict)
    cantBcs: dict[str, list[str]] = field(default_factory=dict)


def equal_default_pidiff(a: DiffEntry, b: DiffEntry):
    match b.kind:
        case "RemoveModule":
            x = a.kind == "RemoveModule" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveExternalModule":
            x = a.kind == "RemoveModule" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "AddModule":
            x = a.kind == "AddModule" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "AddExternalModule":
            x = a.kind == "AddModule" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveAttribute":
            x = a.kind == "RemoveAttribute" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveFunction":
            x = a.kind == "RemoveFunction" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveMethod":
            x = a.kind == "RemoveFunction" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveClass":
            x = a.kind == "RemoveClass" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "AddAttribute":
            x = a.kind == "AddAttribute" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "AddFunction":
            x = a.kind == "AddFunction" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "AddMethod":
            x = a.kind == "AddFunction" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "AddClass":
            x = a.kind == "AddClass" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveParameter":
            return a.kind.startswith("Remove") and a.kind.endswith("Parameter") and a.data["old"] in b.message
        case "AddParameter":
            return a.kind.startswith("Add") and a.kind.endswith("Parameter") and a.data["new"] in b.message
        case "ReorderParameter":
            return a.kind == "ReorderParameter" and a.data["name"] in b.message
        case "UnpositionalParameter":
            x = a.kind == "ReorderParameter" and a.data["name"] in b.message
            y = a.kind.startswith("Remove") and a.kind.endswith(
                "Parameter") and a.data["old"] in b.message
            return x or y
        case "RemoveVarPositional":
            return a.kind == "RemoveVarPositional" and a.old.name in b.message
        case "RemoveVarKeyword":
            return a.kind == "RemoveVarKeyword" and a.old.name in b.message
        case "Uncallable":
            return a.kind == "DeimplementAbstractBaseClass" and "Callable" in a.message
        case "AddOptionalParameter":
            return a.kind == "AddOptionalParameter" and a.data["new"] in b.message
        case "AddParameterDefault":
            return a.kind == "AddParameterDefault" and a.data["new"] in b.message
        case "AddVarPositional":
            return a.kind == "AddVarPositional" and a.old.name in b.message
        case "AddVarKeyword":
            return a.kind == "AddVarKeyword" and a.old.name in b.message


def equal_default_pycompat(a: DiffEntry, b: DiffEntry):
    match b.kind:
        case "AddClass":
            x = a.kind == "AddClass" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveClass":
            x = a.kind == "RemoveClass" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "AddFunction":
            x = a.kind == "AddFunction" and a.new.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveFunction":
            x = a.kind == "RemoveFunction" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y
        case "AddRequiredParameter":
            return a.kind == "AddRequiredParameter" and a.data["new"] in b.message
        case "RemoveRequiredParameter":
            return a.kind == "RemoveRequiredParameter" and a.data["old"] in b.message
        case "ReorderParameter":
            return a.kind == "ReorderParameter" and a.data["name"] in b.message
        case "AddOptionalParameter":
            return a.kind == "AddOptionalParameter" and a.data["new"] in b.message
        case "RemoveOptionalParameter":
            return a.kind == "RemoveOptionalParameter" and a.data["old"] in b.message
        case "AddParameterDefault":
            return a.kind == "AddParameterDefault" and a.data["new"] in b.message
        case "RemoveParameterDefault":
            return a.kind == "RemoveParameterDefault" and a.data["old"] in b.message
        case "ChangeParameterDefault":
            return a.kind == "ChangeParameterDefault" and a.data["old"] in b.message
        case "AddAttribute":
            x = a.kind == "AddAttribute" and a.old.name in b.message
            y = a.kind == "AddAlias" and a.data["name"] in b.message
            return x or y
        case "RemoveAttribute":
            x = a.kind == "RemoveAttribute" and a.old.name in b.message
            y = a.kind == "RemoveAlias" and a.data["name"] in b.message
            return x or y


def diff(default: ApiBreaking, pidiff: ApiBreaking, pycompat: ApiBreaking) -> tuple[list[DiffEntry], list[DiffEntry], list[DiffEntry], list[DiffEntry]]:
    uniques = []
    uniqueBcs = []
    cants = []
    cantBcs = []

    for item in default.entries.values():
        unique = True
        for other in pidiff.entries.values():
            if equal_default_pidiff(item, other):
                unique = False
                break
        if unique:
            for other in pycompat.entries.values():
                if equal_default_pycompat(item, other):
                    unique = False
                    break
        if unique:
            uniques.append(item)
            if item.rank != BreakingRank.Compatible:
                uniqueBcs.append(item)

    for item in pidiff.entries.values():
        can = False
        for other in default.entries.values():
            if equal_default_pidiff(other, item):
                can = True
                break
        if not can:
            cants.append(item)
            if item.rank != BreakingRank.Compatible:
                cantBcs.append(item)

    for item in pycompat.entries.values():
        can = False
        for other in default.entries.values():
            if equal_default_pycompat(other, item):
                can = True
                break
        if not can:
            cants.append(item)
            if item.rank != BreakingRank.Compatible:
                cantBcs.append(item)

    return uniques, uniqueBcs, cants, cantBcs


def main():
    cache = cacheRoot / "diff"

    default = PipelineConfig().build()
    pidiff = getDefaultPidiff().build()
    pycompat = getDefaultPycompat().build()

    def collect(project: str):
        summary = DiffSummary(project=project)

        loaderDefault = BatchLoader(project, default)
        loaderPidiff = BatchLoader(project, pidiff)
        loaderPycompat = BatchLoader(project, pycompat)

        loaderDefault.index()
        loaderPidiff.index()
        loaderPycompat.index()

        donePidiff = {str(x) for x in loaderPidiff.evaluated}
        donePycompat = {str(x) for x in loaderPycompat.evaluated}

        doneAll = []

        for pair in loaderDefault.evaluated:
            st = str(pair)
            if st in donePidiff and st in donePycompat:
                doneAll.append(pair)

        summary.done = [str(x) for x in doneAll]

        for pair in doneAll:
            dataDefault = loaderDefault.eval(pair)
            dataPidiff = loaderPidiff.eval(pair)
            dataPycompat = loaderPycompat.eval(pair)
            summary.alldefault[str(pair)] = len(dataDefault.entries)
            summary.allpidiff[str(pair)] = len(dataPidiff.entries)
            summary.allpycompat[str(pair)] = len(dataPycompat.entries)
            unique, uniqueBc, cant, cantBc = diff(
                dataDefault, dataPidiff, dataPycompat)
            summary.uniques[str(pair)] = [x.message for x in unique]
            summary.uniqueBcs[str(pair)] = [x.message for x in uniqueBc]
            summary.cants[str(pair)] = [x.message for x in cant]
            summary.cantBcs[str(pair)] = [x.message for x in cantBc]

        return summary

    csvs = []
    csvs.append(",".join(["Project", "Unique", "UniqueBC", "Cant", "CantBC",
                "AllDefault", "AllPidiff", "AllPycompat"]))

    for project in defaultProjects:
        print(f"Processing {project}")

        cached = cache / f"{project}.json"

        ensureDirectory(cached.parent)
        if cached.exists():
            summary = DiffSummary(**json.loads(cached.read_text()))
        else:
            summary = collect(project)
            with cached.open("w") as f:
                json.dump(asdict(summary), f, indent=2)

        uniqueCount = sum((len(x) for x in summary.uniques.values()))
        uniqueBcCount = sum((len(x) for x in summary.uniqueBcs.values()))
        cantCount = sum((len(x) for x in summary.cants.values()))
        cantBcCount = sum((len(x) for x in summary.cantBcs.values()))
        allDefaultCount = sum((x for x in summary.alldefault.values()))
        allPidiffCount = sum((x for x in summary.allpidiff.values()))
        allPycompatCount = sum((x for x in summary.allpycompat.values()))

        csvs.append(",".join([project, str(uniqueCount), str(uniqueBcCount), str(cantCount), str(cantBcCount),
                              str(allDefaultCount), str(allPidiffCount), str(allPycompatCount)]))

    cacheRoot.joinpath("diff.csv").write_text("\n".join(csvs))
