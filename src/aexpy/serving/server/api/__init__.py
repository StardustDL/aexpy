
from dateutil.parser import parse
from flask import Blueprint, Response, jsonify, request, send_file, send_from_directory

from aexpy.models import Product, Release, ReleasePair
from aexpy.pipelines import Pipeline
from aexpy.producer import ProducerOptions

api = Blueprint("api", __name__)


def prepare() -> "tuple[Pipeline, ProducerOptions]":
    from aexpy.env import env
    pipeline = env.build(request.args.get("provider", ""))
    options = ProducerOptions()

    # redo = request.args.get("redo", None)
    # onlyCache = request.args.get("onlyCache", None)
    # nocache = request.args.get("nocache", None)

    # if redo is not None:
    #     options.redo = redo == "true" or redo == "1"
    # if onlyCache is not None:
    #     options.onlyCache = onlyCache == "true" or onlyCache == "1"
    # if nocache is not None:
    #     options.nocache = nocache == "true" or nocache == "1"

    if request.method == "GET":
        options.onlyCache = True
    elif request.method == "POST":
        options.redo = True
    elif request.method == "PUT":
        options.nocache = True

    return pipeline, options


def responseData(result: "Product"):
    if request.args.get("log", None):
        text = ""
        if result.logFile:
            text = result.logFile.read_text()
        return Response(text, mimetype="text/plain")
    else:
        return Response(result.dumps(), content_type="application/json")


@api.route("/generating/providers")
def provider():
    from aexpy.env import env, setDefaultPipelineConfig
    defaults = setDefaultPipelineConfig()
    request.method
    return jsonify(list(set(env.pipelines.keys()) | set(defaults.keys())))


@api.route("/generating/releases/<id>", methods=["GET"])
def release(id: str):
    from aexpy.batching.generators import single
    return jsonify(single(id))


@api.route("/generating/pairs/<id>", methods=["GET"])
def pair(id: str):
    from aexpy.batching.generators import pair, single
    return jsonify(pair(single(id)))


@api.route("/preprocessing/<id>", methods=["GET", "POST", "PUT"])
def preprocess(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.preprocess(Release.fromId(id), options=options)
    return responseData(result)


@api.route("/extracting/<id>", methods=["GET", "POST", "PUT"])
def extract(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.extract(Release.fromId(id), options=options)
    return responseData(result)


@api.route("/differing/<id>", methods=["GET", "POST", "PUT"])
def diff(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.diff(ReleasePair.fromId(id), options=options)
    return responseData(result)


@api.route("/evaluating/<id>", methods=["GET", "POST", "PUT"])
def eval(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.eval(ReleasePair.fromId(id), options=options)
    return responseData(result)


@api.route("/reporting/<id>", methods=["GET", "POST", "PUT"])
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


@api.route("/batching/<id>", methods=["GET", "POST", "PUT"])
def batch(id: "str") -> "dict":
    pipeline, options = prepare()
    result = pipeline.batch(id, options=options)
    return responseData(result)


@api.route("/batching/<id>/index", methods=["GET", "POST", "PUT"])
def index(id: "str"):
    pipeline, options = prepare()
    result = pipeline.index(id, options=options)
    return responseData(result)


def build():
    from aexpy.env import env

    data = Blueprint("data", __name__)
    from flask_autoindex import AutoIndex

    # Force all file is text/plain
    AutoIndex._render_autoindex = AutoIndex.render_autoindex
    def render_autoindex(self, path, browse_root=None, template=None, template_context=None, endpoint='.autoindex', show_hidden=None, sort_by='name', order=1, mimetype=None):
        return self._render_autoindex(path, browse_root, template, template_context, endpoint, show_hidden, sort_by, order, mimetype="text/plain")
    AutoIndex.render_autoindex = render_autoindex

    AutoIndex(data, browse_root=str(env.cache))

    api.register_blueprint(data, url_prefix="/data")
    return api
