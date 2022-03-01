import pathlib

import click
import os
import shutil
import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
from flask import request, abort


def buildApp():
    from . import app
    from .api import build as apiBuild
    from .frontend import frontend

    app.register_blueprint(apiBuild(), url_prefix="/api")
    app.register_blueprint(frontend, url_prefix="/")

    return app


def serve(debug: bool = False, port: int = 5000):
    app = buildApp()

    if debug:
        app.run(host="0.0.0.0", port=port, debug=debug)

    else:
        click.echo(f"Listening on port {port}...")
        click.echo(
            f"Visit http://localhost:{port} to Paperead.")

        container = tornado.wsgi.WSGIContainer(app)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(port)
        tornado.ioloop.IOLoop.current().start()
