import code
from typing import Any, Callable, Iterable

import click

import aexpy


def view(items: Iterable):
    for item in items:
        click.echo(str(item))


def interact(locals: dict[str, Any] | None = None, readhook: Callable[[str], str] | None = None):
    locals = locals or {}
    locals = {
        **locals,
        "view": view,
        "aexpy": aexpy,
    }
    varnames = list(locals.keys())
    code.interact(local=locals or {},
                  banner=f"Variables: {varnames}.", readfunc=readhook)
