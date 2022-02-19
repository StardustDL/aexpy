
from aexpy.models import Release, ReleasePair
from aexpy.env import getPipeline


def pre(data: "Release", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.preprocess(data, redo=retry)


def ext(data: "Release", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.extract(data, redo=retry)


def dif(data: "ReleasePair", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.diff(data.old, data.new, redo=retry)


def eva(data: "ReleasePair", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.eval(data.old, data.new, redo=retry)


def rep(data: "ReleasePair", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.report(data.old, data.new, redo=retry)
