
from aexpy.env import Configuration, env, getPipeline
from aexpy.models import Release, ReleasePair
from aexpy.producer import ProducerOptions


def pre(data: "Release", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.preprocess(
            data, options=ProducerOptions(redo=retry)).success
    except:
        exit(1)


def ext(data: "Release", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.extract(
            data, options=ProducerOptions(redo=retry)).success
    except:
        exit(1)


def dif(data: "ReleasePair", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.diff(data, options=ProducerOptions(redo=retry)).success
    except:
        exit(1)


def eva(data: "ReleasePair", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.eval(data, options=ProducerOptions(redo=retry)).success
    except:
        exit(1)


def rep(data: "ReleasePair", options: "Configuration", retry: "bool"):
    try:
        env.reset(options)
        env.prepare()
        pipeline = getPipeline()
        assert pipeline.report(
            data, options=ProducerOptions(redo=retry)).success
    except:
        exit(1)
