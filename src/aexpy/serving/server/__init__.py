import mimetypes
import pathlib
from typing import Optional

from flask import Flask

from flask_cors import CORS
from flask_compress import Compress

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")

app = Flask(__name__, static_folder="wwwroot/static")
CORS(app)
Compress(app)