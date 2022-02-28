
from flask import Blueprint, jsonify, request, Response
from dateutil.parser import parse

from aexpy.models import Product, Release, ReleasePair

api = Blueprint("api", __name__)


def getPipeline():
    from aexpy.env import env
    return env.build(request.args.get("provider", "default"))

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
    pipeline = getPipeline()
    result = pipeline.preprocess(Release.fromId(id))
    return responseData(result)


@api.route("/extracting/<id>", methods=["GET"])
def extract(id: "str") -> "dict":
    pipeline = getPipeline()
    result = pipeline.extract(Release.fromId(id))
    return responseData(result)


@api.route("/diffing/<id>", methods=["GET"])
def diff(id: "str") -> "dict":
    pipeline = getPipeline()
    result = pipeline.diff(ReleasePair.fromId(id))
    return responseData(result)


@api.route("/evaluating/<id>", methods=["GET"])
def eval(id: "str") -> "dict":
    pipeline = getPipeline()
    result = pipeline.eval(ReleasePair.fromId(id))
    return responseData(result)


@api.route("/reporting/<id>", methods=["GET"])
def report(id: "str") -> "dict":
    pipeline = getPipeline()
    result = pipeline.report(ReleasePair.fromId(id))
    if request.args.get("report", None):
        text = ""
        if result.file:
            text = result.file.read_text()
        return Response(text, mimetype="text/plain")
    else:
        return responseData(result)


@api.route("/batching/<id>", methods=["GET"])
def batch(id: "str") -> "dict":
    pipeline = getPipeline()
    result = pipeline.batch(id)
    return responseData(result)


def build():
    return api
