
from flask import Blueprint, jsonify, request, Response
from dateutil.parser import parse

from aexpy.models import Product, Release, ReleasePair
from aexpy.pipelines import Pipeline
from aexpy.producer import ProducerOptions

api = Blueprint("api", __name__)


def prepare() -> "tuple[Pipeline, ProducerOptions]":
    from aexpy.env import env
    pipeline = env.build(request.args.get("provider", ""))
    options = ProducerOptions()

    redo = request.args.get("redo", None)
    onlyCache = request.args.get("onlyCache", None)
    cached = request.args.get("cached", None)

    if redo is not None:
        options.redo = redo == "true" or redo == "1"
    if onlyCache is not None:
        options.onlyCache = onlyCache == "true" or onlyCache == "1"
    if cached is not None:
        options.cached = cached == "true" or cached == "1"
    return pipeline, options


def responseData(result: "Product"):
    if request.args.get("log", None):
        text = ""
        if result.logFile:
            text = result.logFile.read_text()
        return Response(text, mimetype="text/plain")
    else:
        return Response(result.dumps(), content_type="application/json")


@api.route("/preprocessing/<id>", methods=["GET"])
def preprocess(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.preprocess(Release.fromId(id), options=options)
    return responseData(result)


@api.route("/extracting/<id>", methods=["GET"])
def extract(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.extract(Release.fromId(id), options=options)
    return responseData(result)


@api.route("/differing/<id>", methods=["GET"])
def diff(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.diff(ReleasePair.fromId(id), options=options)
    return responseData(result)


@api.route("/evaluating/<id>", methods=["GET"])
def eval(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.eval(ReleasePair.fromId(id), options=options)
    return responseData(result)


@api.route("/reporting/<id>", methods=["GET"])
def report(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.report(ReleasePair.fromId(id), options=options)
    if request.args.get("report", None):
        text = ""
        if result.file:
            text = result.file.read_text()
        return Response(text, mimetype="text/plain")
    else:
        return responseData(result)


@api.route("/batching/<id>", methods=["GET"])
def batch(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.batch(id, options=options)
    return responseData(result)


@api.route("/batching/<id>/index", methods=["GET"])
def index(id: "str"):
    from aexpy.batching.loaders import BatchLoader
    pipeline, options = prepare()
    loader = BatchLoader(provider=pipeline.name)
    result = pipeline.batch(id, options=options, batcher=loader)
    return responseData(result)


def build():
    return api
