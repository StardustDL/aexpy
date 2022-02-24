
from aexpy.env import Options, env, getPipeline
from aexpy.models import Release, ReleasePair
from aexpy.producer import ProducerOptions


def pre(data: "Release", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.preprocess(data, ProducerOptions(redo=retry)).success
    except:
        exit(1)


def ext(data: "Release", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.extract(data, ProducerOptions(redo=retry)).success
    except:
        exit(1)


def dif(data: "ReleasePair", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.diff(data, ProducerOptions(redo=retry)).success
    except:
        exit(1)


def eva(data: "ReleasePair", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.eval(data, ProducerOptions(redo=retry)).success
    except:
        exit(1)


def rep(data: "ReleasePair", options: "Options", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.report(data, ProducerOptions(redo=retry)).success
    except:
        exit(1)
