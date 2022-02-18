import sys

from aexpy.models import Release
from aexpy.third.pycompat.pipeline import Pipeline



def pre(release: "Release", retry: "bool"):
    pipeline = Pipeline()
    return pipeline.preprocess(release, redo=retry)


def ext(release: "Release", retry: "bool"):
    pipeline = Pipeline()
    return pipeline.extract(release, redo=retry)


def dif(old: "Release", new: "Release", retry: "bool"):
    pipeline = Pipeline()
    return pipeline.diff(old, new, redo=retry)


def eva(old: "Release", new: "Release", retry: "bool"):
    pipeline = Pipeline()
    return pipeline.eval(old, new, redo=retry)


def rep(old: "Release", new: "Release", retry: "bool"):
    pipeline = Pipeline()
    return pipeline.report(old, new, redo=retry)
