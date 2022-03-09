import pathlib

from flask import Blueprint, send_file, send_from_directory

wwwroot = pathlib.Path(__file__).parent.joinpath("wwwroot")

frontend = Blueprint("frontend", __name__)


@frontend.route("/", methods=["GET"])
@frontend.route("/<path:path>", methods=["GET"])
def wwwrootFiles(path: str = "index.html"):
    return send_from_directory(wwwroot, path)


@frontend.errorhandler(404)
def pageNotFound(error):
    return send_file(wwwroot.joinpath("index.html"))
