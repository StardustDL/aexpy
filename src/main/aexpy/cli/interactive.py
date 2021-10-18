import code
from typing import Any, Dict, Iterable, Optional

import click

import aexpy


def view(items: Iterable):
    for item in items:
        click.echo(str(item))


def interact(locals: Optional[Dict[str, Any]] = None):
    locals = locals or {}
    locals = {
        **locals,
        "view": view,
        "aexpy": aexpy,
    }
    varnames = list(locals.keys())
    code.interact(local=locals or {}, banner=f"Variables: {varnames}.")
