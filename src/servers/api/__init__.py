import os
from pathlib import Path

from flask import (Blueprint, Response, jsonify, request, send_file,
                   send_from_directory)

WWW_DATA = Path(__file__).parent.parent.joinpath("wwwdata")


api = Blueprint("api", __name__)


@api.route("/data/<path:path>", methods=["GET"])
def wwwrootFiles(path: str = "index.html"):
    if not WWW_DATA.is_dir():
        os.makedirs(WWW_DATA, exist_ok=True)
    return send_from_directory(WWW_DATA, path)


@api.route("/tasks/extract", methods=["POST"])
def extract():
    return ""


@api.route("/tasks/diff", methods=["POST"])
def diff():
    return ""


@api.route("/info", methods=["GET"])
def info():
    from aexpy import BUILD_DATE, COMMIT_ID

    return jsonify(
        {
            "commitId": COMMIT_ID,
            "buildDate": BUILD_DATE.isoformat(),
        }
    )


def build(wwwdata: Path | None = None):
    if wwwdata:
        global WWW_DATA
        WWW_DATA = wwwdata
    return api
