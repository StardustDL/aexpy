
from dateutil.parser import parse
from flask import Blueprint, Response, jsonify, request, send_file, send_from_directory

from aexpy.models import BatchRequest, Product, Release, ReleasePair
from aexpy.pipelines import Pipeline
from aexpy.services import ProduceMode
from aexpy.env import env

api = Blueprint("api", __name__)


def prepare() -> "tuple[Pipeline, ProduceMode]":
    pipeline = env.build(request.args.get("pipeline", ""))
    mode = ProduceMode.Access

    if request.method == "GET":
        mode = ProduceMode.Read
    elif request.method == "POST":
        mode = ProduceMode.Write
    elif request.method == "PUT":
        mode = ProduceMode.Access

    return pipeline, mode


def responseData(result: "Product"):
    if request.args.get("log", None):
        text = ""
        if result.logFile:
            text = result.logFile.read_text()
        return Response(text, mimetype="text/plain")
    else:
        return Response(result.dumps(), content_type="application/json")


@api.route("/generate/pipelines")
def pipelines():
    from aexpy.env import env, setDefaultPipelineConfig
    defaults = setDefaultPipelineConfig()
    return jsonify(list(set(env.pipelines.keys()) | set(defaults.keys())))


@api.route("/generate/releases/<id>", methods=["GET"])
def release(id: str):
    from aexpy.batching.generators import single
    return jsonify(single(id))


@api.route("/generate/pairs/<id>", methods=["GET"])
def pair(id: str):
    from aexpy.batching.generators import pair, single
    return jsonify(pair(single(id)))


@api.route("/preprocess/<id>", methods=["GET", "POST", "PUT"])
def preprocess(id: "str") -> "dict":
    pipeline, mode = prepare()
    release = Release.fromId(id)
    if request.args.get("log", None):
        return Response(env.services.logPreprocess(pipeline.preprocessor.name, release), mimetype="text/plain")
    return Response(pipeline.preprocess(release, mode=mode).dumps(), content_type="application/json")


@api.route("/extract/<id>", methods=["GET", "POST", "PUT"])
def extract(id: "str") -> "dict":
    pipeline, mode = prepare()
    release = Release.fromId(id)
    if request.args.get("log", None):
        return Response(env.services.logExtract(pipeline.extractor.name, release), mimetype="text/plain")
    return Response(pipeline.extract(release, mode=mode).dumps(), content_type="application/json")


@api.route("/diff/<id>", methods=["GET", "POST", "PUT"])
def diff(id: "str") -> "dict":
    pipeline, mode = prepare()
    pair = ReleasePair.fromId(id)
    if request.args.get("log", None):
        return Response(env.services.logDiff(pipeline.differ.name, pair), mimetype="text/plain")
    return Response(pipeline.diff(pair, mode=mode).dumps(), content_type="application/json")


@api.route("/report/<id>", methods=["GET", "POST", "PUT"])
def report(id: "str") -> "dict":
    pipeline, mode = prepare()
    pair = ReleasePair.fromId(id)
    if request.args.get("log", None):
        return Response(env.services.logReport(pipeline.reporter.name, pair), mimetype="text/plain")
    return Response(pipeline.report(pair, mode=mode).dumps(), content_type="application/json")


@api.route("/batch/<id>", methods=["GET", "POST", "PUT"])
def batch(id: "str") -> "dict":
    pipeline, mode = prepare()
    bat = BatchRequest(project=id)
    if request.args.get("index", None):
        bat.index = True
    if request.args.get("log", None):
        return Response(env.services.logBatch(pipeline.batcher.name, bat), mimetype="text/plain")
    return Response(pipeline.batch(bat, mode=mode).dumps(), content_type="application/json")


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
