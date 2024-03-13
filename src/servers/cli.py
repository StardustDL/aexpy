import click
from pathlib import Path


@click.command()
@click.option(
    "--data",
    type=click.Path(
        exists=True,
        file_okay=False,
        resolve_path=True,
        dir_okay=True,
        path_type=Path,
    ),
    default=None,
    envvar="AEXPY_SERVER_DATA",
    help="Path to data storage directory.",
)
@click.option("-d", "--debug", is_flag=True, help="Debug mode.")
@click.option("-p", "--port", type=int, default=8008, help="Port to listen on.")
def serve(data: Path | None = None, debug: bool = False, port: int = 8008):
    """Serve web server."""
    from .entrypoint import serve as inner, buildApp

    inner(buildApp(data), debug, port)
