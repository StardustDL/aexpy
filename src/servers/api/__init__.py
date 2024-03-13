import os
from pathlib import Path
from flask import Blueprint, Response, jsonify, request, send_file, send_from_directory

wwwdata = Path(__file__).parent.parent.joinpath("wwwdata")

if not wwwdata.is_dir():
    os.makedirs(wwwdata, exist_ok=True)

api = Blueprint("api", __name__)


@api.route("/data/<path:path>", methods=["GET"])
def wwwrootFiles(path: str = "index.html"):
    return send_from_directory(wwwdata, path)


@api.route("/tasks/extract", methods=["POST"])
def extract():
    return ""


@api.route("/tasks/diff", methods=["POST"])
def diff():
    return ""


@api.route("/info", methods=["GET"])
def info():
    from aexpy import COMMIT_ID, BUILD_DATE

    return jsonify(
        {
            "commitId": COMMIT_ID,
            "buildDate": BUILD_DATE.isoformat(),
        }
    )
