import os
import pathlib
import shutil

import click
import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
from flask import Blueprint, abort, request


def buildApp():
    from . import app
    from .api import build as apiBuild
    from .frontend import frontend

    app.register_blueprint(apiBuild(), url_prefix="/api")
    app.register_blueprint(frontend, url_prefix="/")

    return app


def serve(debug: bool = False, port: int = 8008, user: "str" = "", password: "str" = ""):
    app = buildApp()

    if user and password:
        app.config["BASIC_AUTH_USERNAME"] = user
        app.config["BASIC_AUTH_PASSWORD"] = password
        app.config["BASIC_AUTH_FORCE"] = True

        from flask_basicauth import BasicAuth
        BasicAuth(app)

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
