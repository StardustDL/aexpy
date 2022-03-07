from dataclasses import dataclass, field, asdict
from json import load
from aexpy import json
from pathlib import Path

from aexpy import setCacheDirectory
from aexpy.batching.loaders import BatchLoader
from aexpy.env import PipelineConfig
from aexpy.models import Release
from aexpy.models.difference import BreakingRank
from aexpy.pipelines import Pipeline
from aexpy.utils import ensureDirectory
from . import defaultProjects, cacheRoot

providers = ["pidiff", "pycompat", "default"]


@dataclass
class ProjectSummary:
    project: str

    releases: list[str] = field(default_factory=list)
    preprocessed: list[str] = field(default_factory=list)
    extracted: list[str] = field(default_factory=list)
    pairs: list[str] = field(default_factory=list)
    diffed: list[str] = field(default_factory=list)
    evaluated: list[str] = field(default_factory=list)
    reported: list[str] = field(default_factory=list)

    duration_preprocessed: dict[str, float] = field(default_factory=dict)
    duration_extracted: dict[str, float] = field(default_factory=dict)
    duration_diffed: dict[str, float] = field(default_factory=dict)
    duration_evaluated: dict[str, float] = field(default_factory=dict)
    duration_reported: dict[str, float] = field(default_factory=dict)

    entries: dict[str, dict[str, int]] = field(default_factory=dict)
    types: dict[str, list[str]] = field(default_factory=dict)
    typecounts: dict[str, int] = field(default_factory=dict)
    kwargcount: dict[str, int] = field(default_factory=dict)

    kinds: dict[str, dict[str, int]] = field(default_factory=dict)

    bcs: dict[str, dict[str, int]] = field(default_factory=dict)


def collect(project: str, pipeline: Pipeline | str = "default"):
    if isinstance(pipeline, str):
        match pipeline:
            case "default":
                pipeline = PipelineConfig().build()
            case "pidiff":
                from aexpy.third.pidiff.pipeline import getDefault
                pipeline = getDefault().build()
            case "pycompat":
                from aexpy.third.pycompat.pipeline import getDefault
                pipeline = getDefault().build()
            case _:
                raise ValueError(f"Unknown pipeline: {pipeline}")

    loader = BatchLoader(project, pipeline)
    loader.index()

    summary = ProjectSummary(project)

    summary.releases = [str(r) for r in loader.releases]
    summary.preprocessed = [str(r) for r in loader.preprocessed]
    summary.extracted = [str(r) for r in loader.extracted]
    summary.pairs = [str(r) for r in loader.pairs]
    summary.diffed = [str(r) for r in loader.diffed]
    summary.evaluated = [str(r) for r in loader.evaluated]
    summary.reported = [str(r) for r in loader.reported]

    for item in loader.preprocessed:
        data = loader.preprocess(item)
        summary.duration_preprocessed[str(
            item)] = data.duration.total_seconds()

    for item in loader.extracted:
        data = loader.extract(item)
        summary.duration_extracted[str(item)] = data.duration.total_seconds()
        summary.entries[str(item)] = {
            "entries": len(data.entries),
            "modules": len(data.modules),
            "classes": len(data.classes),
            "funcs": len(data.funcs),
            "attrs": len(data.attrs),
        }

        kwcount = 0
        typecount = 0
        types = set()

        for func in data.funcs.values():
            if func.varKeyword:
                kwcount += 1
            for par in func.parameters:
                if par.type:
                    types.add(par.type.type)
            for par in func.parameters:
                if par.type:
                    typecount += 1
                    break
            if func.type:
                types.add(func.type.type)

        for attr in data.attrs.values():
            if attr.type:
                types.add(attr.type.type)

        summary.types[str(item)] = list(types)
        summary.typecounts[str(item)] = typecount
        summary.kwargcount[str(item)] = kwcount

    for item in loader.diffed:
        data = loader.diff(item)
        summary.duration_diffed[str(item)] = data.duration.total_seconds()

    for item in loader.evaluated:
        data = loader.eval(item)
        summary.duration_evaluated[str(item)] = data.duration.total_seconds()
        summary.bcs[str(item)] = {rank.name: len(
            data.rank(rank)) for rank in BreakingRank if rank > BreakingRank.Compatible}
        kinds = data.kinds()
        summary.kinds[str(item)] = {
            k: len(data.kind(k)) for k in kinds
        }

    for item in loader.reported:
        data = loader.report(item)
        summary.duration_reported[str(item)] = data.duration.total_seconds()

    return summary


def main():
    csvs = []
    csvs.append(",".join(["Provider", "Project", "Release", "Preprocessed", "Extracted", "Pairs", "Diffed", "Evaluated",
                "Reported", "Duration", "Entries", "Modules", "Classes", "Funcs", "Attrs", "Typed funcs", "Kwarg funcs", "Changes", "BCs"]))

    for provider in ["pidiff", "pycompat", "default"]:
        cache = cacheRoot / provider

        ensureDirectory(cache)

        for project in defaultProjects:
            print(f"Summary {provider}'s {project}")

            cached = cache.joinpath(f"{project}.json")
            if cached.exists():
                summary = ProjectSummary(**json.loads(cached.read_text()))
            else:
                summary = collect(project, provider)
                with cached.open("w") as f:
                    json.dump(asdict(summary), f, indent=2)

            cntReleases = len(summary.releases)
            cntPreprocessed = len(summary.preprocessed)
            cntExtracted = len(summary.extracted)
            cntPairs = len(summary.pairs)
            cntDiffed = len(summary.diffed)
            cntEvaluated = len(summary.evaluated)
            cntReported = len(summary.reported)
            avgdurationPreprocessed = sum(summary.duration_preprocessed.values(
            )) / cntPreprocessed if cntPreprocessed > 0 else 0
            avgdurationExtracted = sum(
                summary.duration_extracted.values()) / cntExtracted if cntExtracted > 0 else 0
            avgdurationDiffed = sum(
                summary.duration_diffed.values()) / cntDiffed if cntDiffed > 0 else 0
            avgdurationEvaluated = sum(
                summary.duration_evaluated.values()) / cntEvaluated if cntEvaluated > 0 else 0
            avgdurationReported = sum(
                summary.duration_reported.values()) / cntReported if cntReported > 0 else 0
            avgdurationAll = (avgdurationPreprocessed + avgdurationExtracted +
                            avgdurationDiffed + avgdurationEvaluated + avgdurationReported)

            avgEntries = sum(
                (val['entries'] for val in summary.entries.values())) / len(summary.entries)
            avgModules = sum(
                (val['modules'] for val in summary.entries.values())) / len(summary.entries)
            avgClasses = sum(
                (val['classes'] for val in summary.entries.values())) / len(summary.entries)
            avgFuncs = sum(
                (val['funcs'] for val in summary.entries.values())) / len(summary.entries)
            avgAttrs = sum(
                (val['attrs'] for val in summary.entries.values())) / len(summary.entries)

            avgTypeKinds = sum(
                (len(val) for val in summary.types.values())) / len(summary.types)
            avgTypeCounts = sum(summary.typecounts.values()) / \
                len(summary.typecounts)
            avgKwargCounts = sum(summary.kwargcount.values()
                                ) / len(summary.kwargcount)

            report = []
            report.append(f"Project: {project}, provider: {provider}")
            report.append(f"Releases: {cntReleases}")
            report.append(f"Preprocessed: {cntPreprocessed}")
            report.append(f"Extracted: {cntExtracted}")
            report.append(f"Pairs: {cntPairs}")
            report.append(f"Diffed: {cntDiffed}")
            report.append(f"Evaluated: {cntEvaluated}")
            report.append(f"Reported: {cntReported}")

            report.append("")
            report.append("Duration")
            report.append(f"Average Preprocessed: {avgdurationPreprocessed}s")
            report.append(f"Average Extracted: {avgdurationExtracted}s")
            report.append(f"Average Diffed: {avgdurationDiffed}s")
            report.append(f"Average Evaluated: {avgdurationEvaluated}s")
            report.append(f"Average Reported: {avgdurationReported}s")
            report.append(f"Average All: {avgdurationAll}s")

            report.append("")
            report.append(f"Average Entries: {avgEntries}")
            report.append(f"Average Modules: {avgModules}")
            report.append(f"Average Classes: {avgClasses}")
            report.append(f"Average Functions: {avgFuncs}")
            report.append(f"Average Attributes: {avgAttrs}")

            report.append("")
            report.append(
                f"Average Type kinds: {avgTypeKinds}")
            report.append(
                f"Average Typed functions: {avgTypeCounts}")
            report.append(
                f"Average Kwarg functions: {avgKwargCounts}")

            changes = 0

            report.append("")
            kinds = set()
            for item in summary.kinds.values():
                kinds.update(item.keys())
            for item in kinds:
                cnt = sum((val[item]
                        for val in summary.kinds.values() if item in val))
                report.append(
                    f"Change {item}: {cnt}")
                changes += cnt
            report.append(f"Changes: {changes}")

            bcs = 0

            report.append("")
            for rank in BreakingRank:
                cnt = sum((val[rank.name]
                        for val in summary.bcs.values() if rank.name in val))
                report.append(
                    f"Breaking {rank.name}: {cnt}")
                bcs += cnt
            report.append(f"Breaking: {bcs}")

            cache.joinpath(f"{project}.txt").write_text("\n".join(report))

            csvs.append(",".join(map(str, [provider, project, cntReleases, cntPreprocessed, cntExtracted, cntPairs, cntDiffed, cntEvaluated,
                        cntReported, avgdurationAll, avgEntries, avgModules, avgClasses, avgFuncs, avgAttrs, avgTypeCounts, avgKwargCounts, changes, bcs])))

    cacheRoot.joinpath("summary.csv").write_text("\n".join(csvs))
