import os
import shutil
from pathlib import Path

import click
import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
from flask import Flask


def buildApp(wwwdata: Path | None = None):
    from . import app
    from .api import build
    from .frontend import frontend

    app.register_blueprint(build(wwwdata), url_prefix="/api")
    app.register_blueprint(frontend, url_prefix="/")

    return app


def serve(app: Flask, debug: bool = False, port: int = 8008):
    if debug:
        app.run(host="0.0.0.0", port=port, debug=debug)

    else:
        click.echo(f"Listening on port {port}...")
        click.echo(f"Visit http://localhost:{port} to AexPy.")

        container = tornado.wsgi.WSGIContainer(app)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(port)
        tornado.ioloop.IOLoop.current().start()
