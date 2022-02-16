import sys

from aexpy.models import Release

from .releases import projects

from .single import SingleProcessor
from .pair import PairProcessor

from third.pidiff.pipelines import getPipeline


def pre(release: "Release"):
    pipeline = getPipeline()
    return pipeline.preprocess(release, redo=True)


def ext(release: "Release"):
    pipeline = getPipeline()
    return pipeline.extract(release, redo=True)


def dif(old: "Release", new: "Release"):
    pipeline = getPipeline()
    return pipeline.diff(old, new, redo=True)


def eva(old: "Release", new: "Release"):
    pipeline = getPipeline()
    return pipeline.eval(old, new, redo=True)


def rep(old: "Release", new: "Release"):
    pipeline = getPipeline()
    return pipeline.report(old, new, redo=True)
