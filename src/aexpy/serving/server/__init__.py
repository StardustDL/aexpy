import mimetypes
import pathlib
from typing import Optional

from flask import Flask
from flask_compress import Compress
from flask_cors import CORS

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")

app = Flask(__name__, static_folder="wwwroot/static")
CORS(app)
Compress(app)
