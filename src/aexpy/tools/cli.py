import logging
import pkgutil
from logging import Logger
from pathlib import Path

import click

from ..cli import AliasedGroup


@click.group(cls=AliasedGroup)
@click.pass_context
def tool(
    ctx: click.Context,
) -> None:
    """Advanced tools

    The command name 'tool' can be omitted, directly using the name of subcommands."""
    pass


def build(
    path: str = "", name: str = "", logger: Logger | None = None
) -> list[click.Command]:
    logger = logger or logging.getLogger("cmd-loader")
    import importlib

    mainCommand = tool

    root = Path(path) if path else Path(__file__).parent
    name = name or __name__.rsplit(".", maxsplit=1)[0]
    for sub in pkgutil.iter_modules(path=[str(root)], prefix=""):
        if not sub.ispkg:
            continue
        for ssub in pkgutil.iter_modules(path=[str(root / sub.name)], prefix=""):
            if ssub.name != "cli":
                continue
            cmds: list[click.Command] = []
            modname = f"{name or __name__}.{sub.name}.{ssub.name}"
            try:
                climod = importlib.import_module(modname)
                subBuild = getattr(climod, "build", None)
                if subBuild:
                    cmds.extend(subBuild(logger=logger))
                else:
                    for item in dir(climod):
                        subval = getattr(climod, item)
                        if isinstance(subval, click.Command):
                            cmds.append(subval)
            except Exception:
                logger.error(f"Failed to load {modname}", exc_info=True)
            logger.debug(f"Found commands under {modname}: {cmds}")
            for cmd in cmds:
                mainCommand.add_command(cmd)
    return [mainCommand]
