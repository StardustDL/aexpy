
from aexpy.models import Release, ReleasePair
from aexpy.env import getPipeline, Options, env


def pre(data: "Release", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.preprocess(data, redo=retry).success
    except:
        exit(1)


def ext(data: "Release", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.extract(data, redo=retry).success
    except:
        exit(1)


def dif(data: "ReleasePair", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.diff(data, redo=retry).success
    except:
        exit(1)


def eva(data: "ReleasePair", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.eval(data, redo=retry).success
    except:
        exit(1)


def rep(data: "ReleasePair", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.report(data, redo=retry).success
    except:
        exit(1)
