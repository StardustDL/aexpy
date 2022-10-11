
from aexpy.env import Configuration, env, getPipeline
from aexpy.models import ProduceMode, Release, ReleasePair
from aexpy.producers import ProducerOptions


def pre(data: "Release", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.preprocess(
            data, ProduceMode.Read).success
    except:
        exit(1)


def ext(data: "Release", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.extract(
            data, ProduceMode.Read).success
    except:
        exit(1)


def dif(data: "ReleasePair", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.diff(
            data, ProduceMode.Read).success
    except:
        exit(1)


def rep(data: "ReleasePair", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.report(
            data, ProduceMode.Read).success
    except:
        exit(1)
