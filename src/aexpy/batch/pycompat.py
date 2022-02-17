import sys

from aexpy.models import Release
from aexpy.third.pycompat.pipeline import Pipeline


def pre(release: "Release"):
    pipeline = Pipeline()
    return pipeline.preprocess(release, redo=True)


def ext(release: "Release"):
    pipeline = Pipeline()
    return pipeline.extract(release, redo=True)


def dif(old: "Release", new: "Release"):
    pipeline = Pipeline()
    return pipeline.diff(old, new, redo=True)


def eva(old: "Release", new: "Release"):
    pipeline = Pipeline()
    return pipeline.eval(old, new, redo=True)


def rep(old: "Release", new: "Release"):
    pipeline = Pipeline()
    return pipeline.report(old, new, redo=True)
