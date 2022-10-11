import functools
import sys
from typing import Callable

import semver
from packaging import version as pkgVersion

from aexpy.diffing import Differ
from aexpy.extracting import Extractor
from aexpy.models import ProduceMode, Release, ReleasePair
from aexpy.pipelines import Pipeline
from aexpy.preprocessing import Preprocessor
from aexpy.producers import ProducerOptions

projects = ["urllib3", "python-dateutil", "requests", "pyyaml", "jmespath",
            "numpy", "click", "pandas", "flask", "tornado", "django", "scrapy", "coxbuild"]


def single(project: str, filter: "Callable[[Release], bool] | None" = None) -> "list[Release]":
    from aexpy.preprocessing.wheel import WheelPreprocessor

    prep = WheelPreprocessor()

    rels: "list[Release]" = []

    raw = prep.getReleases(project)
    if raw:
        for version in raw:
            rel = Release(project, version)
            if filter:
                if not filter(rel):
                    continue
            rels.append(rel)

    versions = rels.copy()
    try:
        versions.sort(key=functools.cmp_to_key(lambda x,y: compareVersion(x.version, y.version)))
    except Exception as ex:
        versions = rels.copy()
        # print(f"  Failed to sort versions by packaging.version: {versions} Exception: {ex}", file=sys.stderr)
        try:
            versions.sort(key=functools.cmp_to_key(lambda x,y: semver.compare(x.version, y.version)))
        except Exception as ex:
            versions = rels.copy()
            # print(f"  Failed to sort versions by semver: {versions} Exception: {ex}", file=sys.stderr)

    return versions


def preprocessed(pipeline: "Pipeline"):
    def filter(release: "Release") -> "bool":
        try:
            return pipeline.preprocess(release, ProduceMode.Read).success
        except:
            return False

    return filter


def extracted(pipeline: "Pipeline"):
    def filter(release: "Release") -> "bool":
        try:
            return pipeline.extract(release, ProduceMode.Read).success
        except:
            return False

    return filter


def diffed(pipeline: "Pipeline"):
    def filter(releasePair: "ReleasePair") -> "bool":
        try:
            return pipeline.diff(releasePair, ProduceMode.Read).success
        except:
            return False

    return filter


def reported(pipeline: "Pipeline"):
    def filter(releasePair: "ReleasePair") -> "bool":
        try:
            return pipeline.report(releasePair, ProduceMode.Read).success
        except:
            return False

    return filter


def compareVersion(a, b):
    a = pkgVersion.parse(a)
    b = pkgVersion.parse(b)
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0


def pair(releases: "list[Release]", filter: "Callable[[ReleasePair], bool] | None" = None) -> "list[ReleasePair]":
    rels = releases

    ret: "list[ReleasePair]" = []

    lastVersion: "Release | None" = None
    for item in rels:
        if lastVersion is None:
            pass
        else:
            rp = ReleasePair(lastVersion, item)

            if filter:
                if not filter(rp):
                    continue

            ret.append(rp)
        lastVersion = item

    return ret
