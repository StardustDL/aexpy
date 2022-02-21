
from aexpy.models import Release, ReleasePair
from aexpy.env import getPipeline


def pre(data: "Release", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.preprocess(data, redo=retry).success


def ext(data: "Release", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.extract(data, redo=retry).success


def dif(data: "ReleasePair", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.diff(data, redo=retry).success


def eva(data: "ReleasePair", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.eval(data, redo=retry).success


def rep(data: "ReleasePair", retry: "bool"):
    pipeline = getPipeline()
    return pipeline.report(data, redo=retry).success
