import mimetypes

from flask import Flask
from flask_compress import Compress
from flask_cors import CORS

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")

app = Flask(__name__)
CORS(app)
Compress(app)
