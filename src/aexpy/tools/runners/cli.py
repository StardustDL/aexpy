from pathlib import Path

import click

from ...cli import CliContext
from . import AexPyDockerRunner


@click.command()
@click.pass_context
@click.option(
    "-v",
    "--volume",
    type=click.Path(
        exists=True, dir_okay=True, file_okay=False, resolve_path=True, path_type=Path
    ),
    default=Path("."),
)
@click.option(
    "-t",
    "--tag",
    default="",
    help="Image tag, empty to use the same version as current.",
)
@click.argument(
    "args",
    nargs=-1,
)
def runimage(
    ctx: click.Context, args: tuple[str], volume: Path = Path("."), tag: str = ""
):
    """Quick runner to execute commands using AexPy images.

    VOLUME describes the mount directory for containers (to /data), default using current working directory.

    All file path arguments passed to container should use absolute paths with `/data` prefix or use a path relative to `/data`.

    Examples:

    aexpy tool runimage -v ./mount -- --version

    aexpy runimage -v ./mount -- extract ./dist.json ./api.json

    aexpy runimage -v ./mount -- extract /data/dist.json /data/api.json
    """
    clictx = ctx.ensure_object(CliContext)

    runner = AexPyDockerRunner(
        cwd=volume,
        cli=clictx,
        tag=tag,
    )

    result = runner.run(list(args), capture_output=False)

    exit(result.returncode)
