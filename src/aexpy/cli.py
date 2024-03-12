import code
import json
import logging
import sys
import zipfile
from dataclasses import dataclass
from io import BytesIO, TextIOWrapper
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import IO, Any, Literal, cast, override

import click

from . import (__version__, getBuildDate, getShortCommitId, initializeLogging,
               runInContainer)
from .models import (ApiDescription, ApiDifference, Distribution, ProduceState,
                     Product, Release, Report)
from .producers import ProduceContext, produce
from .services import ServiceProvider, getService, loadServiceFromCode
from .tools.models import StatSummary

DEFAULT_SERVICE = getService()


@dataclass
class CliContext:
    verbose: int = 0
    interact: bool = False
    gzip: bool = False
    service: ServiceProvider = DEFAULT_SERVICE


class AliasedGroup(click.Group):
    @override
    def get_command(self, /, ctx: click.Context, cmd_name: str):
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [
            (x, super().get_command(ctx, x))
            for x in self.list_commands(ctx)
            if x.startswith(cmd_name)
        ]
        if not matches:
            matches = [
                (y, cast(click.Group, super().get_command(ctx, x)).get_command(ctx, y))
                for x in self.list_commands(ctx)
                if isinstance(super().get_command(ctx, x), click.Group)
                for y in cast(click.Group, super().get_command(ctx, x)).list_commands(
                    ctx
                )
                if y.startswith(cmd_name)
            ]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0][1]

        ctx.fail(
            f"Too many command matches: {', '.join(sorted([n for n, _ in matches]))}"
        )

    def resolve_command(
        self, /, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        assert cmd is not None, "Command is None."
        return cmd.name, cmd, args


def StreamProductLoader(stream: IO[bytes]):
    from .io.gzip import GzipStreamAutoProductLoader

    return GzipStreamAutoProductLoader(stream)


def StreamProductSaver(
    target: IO[bytes], logStream: IO[bytes] | None = None, gzip: bool = False
):
    if gzip:
        from .io.gzip import GzipStreamProductSaver

        return GzipStreamProductSaver(target, logStream)
    else:
        from .io import StreamProductSaver

        return StreamProductSaver(target, logStream)


def exitWithContext[T: Product](context: ProduceContext[T]):
    if context.product.state == ProduceState.Success:
        exit(0)
    print(f"Failed to process: {context.exception}", file=sys.stderr)
    exit(1)


def versionMessage():
    parts = [
        "%(prog)s v%(version)s",
        getShortCommitId(),
        str(getBuildDate().date()),
    ]
    if runInContainer():
        parts.append("in-container")
    return ", ".join(parts)


@click.group(cls=AliasedGroup)
@click.pass_context
@click.version_option(
    __version__,
    package_name="aexpy",
    prog_name="aexpy",
    message=versionMessage(),
)
@click.option(
    "-s",
    "--service",
    type=click.File("r"),
    default=None,
    envvar="AEXPY_SERVICE",
    help="Customized service provider.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    type=click.IntRange(0, 5),
    help="Increase verbosity.",
)
@click.option("-i", "--interact", is_flag=True, default=False, help="Interact mode.")
@click.option(
    "--gzip/--no-gzip",
    is_flag=True,
    default=False,
    envvar="AEXPY_GZIP_IO",
    help="Gzip for IO.",
)
def main(
    ctx: click.Context,
    verbose: int = 0,
    interact: bool = False,
    gzip: bool = False,
    service: IO[str] | None = None,
) -> None:
    """
    AexPy /eɪkspaɪ/ is Api EXplorer in PYthon for detecting API breaking changes in Python packages. (ISSRE'22)

    Home page: https://aexpy.netlify.app/

    Repository: https://github.com/StardustDL/aexpy
    """

    clictx = ctx.ensure_object(CliContext)
    clictx.verbose = verbose
    clictx.interact = interact
    clictx.gzip = gzip

    loggingLevel = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.NOTSET,
    }[verbose]

    initializeLogging(loggingLevel)

    logger = logging.getLogger()

    if service is not None:
        try:
            clictx.service = loadServiceFromCode(service.read())
            logger.info(f"Loaded service {clictx.service.name}: {clictx.service}")
        except Exception:
            logger.critical(
                "Failed to load service, please ensure the code define a function named `getService` and return a ServiceProvider.",
                exc_info=True,
            )
            exit(1)


def preprocessCore(
    service: ServiceProvider,
    path: Path,
    module: list[str] | None = None,
    project: str = "",
    pyversion: str = "",
    depends: list[str] | None = None,
    requirements: Path | None = None,
    mode: (
        Literal["src"] | Literal["dist"] | Literal["wheel"] | Literal["release"]
    ) = "src",
):
    from .models import Distribution

    dependencies = list(depends or [])
    if requirements:
        dependencies.extend(
            [
                s.strip()
                for s in requirements.read_text().strip().splitlines()
                if s.strip()
            ]
        )

    with produce(
        Distribution(
            release=Release.fromId(project),
            rootPath=path,
            topModules=list(module or []),
            dependencies=dependencies,
            pyversion=pyversion,
        ),
        service=service.name,
    ) as context:
        if mode == "release":
            assert path.is_dir(), "The cache path should be a directory."
            assert (
                context.product.release.project and context.product.release.version
            ), "Please give the release ID."
            from .preprocessing.download import PipWheelDownloadPreprocessor

            with context.using(PipWheelDownloadPreprocessor(cacheDir=path)) as producer:
                producer.preprocess(context.product)
            mode = "wheel"

        if mode == "wheel":
            from .preprocessing.wheel import WheelUnpackPreprocessor

            if path.is_file():
                # a path to wheel file
                context.product.wheelFile = path
                path = path.parent
            else:
                # a cache path, from release download
                assert context.product.wheelFile, "The wheel path should be a file."
            with context.using(WheelUnpackPreprocessor(cacheDir=path)) as producer:
                producer.preprocess(context.product)
            mode = "dist"

        if mode == "dist":
            assert path.is_dir(), "The target path should be a directory."
            from .preprocessing.wheel import WheelMetadataPreprocessor

            with context.using(WheelMetadataPreprocessor()) as producer:
                producer.preprocess(context.product)
            mode = "src"

        assert mode == "src"
        assert path.is_dir(), "The target path should be a directory."

        context = service.preprocess(
            context.product, logger=context.logger, context=context
        )
        if not context.product.pyversion:
            context.product.pyversion = "3.12"

    return context


def extractCore(
    service: ServiceProvider,
    data: Distribution,
    env: str = "",
    temp: bool = False,
):
    with produce(ApiDescription(distribution=data), service=service.name) as context:
        if env:
            from .environments import SingleExecutionEnvironmentBuilder
            from .extracting.environment import getExtractorEnvironment

            envBuilder = SingleExecutionEnvironmentBuilder(
                getExtractorEnvironment(env, context.logger), context.logger
            )
        elif temp:
            envBuilder = service.environmentBuilder(logger=context.logger)
        else:
            from .environments import (CurrentEnvironment,
                                       SingleExecutionEnvironmentBuilder)

            envBuilder = SingleExecutionEnvironmentBuilder(
                CurrentEnvironment(context.logger), context.logger
            )

        context = service.extract(
            data, logger=context.logger, context=context, envBuilder=envBuilder
        )

    return context


@main.command()
@click.pass_context
@click.argument(
    "path",
    type=click.Path(
        exists=True,
        file_okay=True,
        resolve_path=True,
        dir_okay=True,
        path_type=Path,
    ),
)
@click.argument("distribution", type=click.File("wb"))
@click.option("-m", "--module", multiple=True, help="Top level module names.")
@click.option(
    "-p", "--project", default="", help="Release string, e.g. project, project@version"
)
@click.option("-P", "--pyversion", default="", help="Python version.")
@click.option("-D", "--depends", multiple=True, help="Package dependency.")
@click.option(
    "-R",
    "--requirements",
    type=click.Path(
        exists=True,
        file_okay=True,
        resolve_path=True,
        dir_okay=False,
        path_type=Path,
    ),
    default=None,
    help="Package requirements file.",
)
@click.option(
    "-s",
    "--src",
    "mode",
    flag_value="src",
    default=True,
    help="Source code directory mode.",
)
@click.option(
    "-d", "--dist", "mode", flag_value="dist", help="Distribution directory mode."
)
@click.option("-w", "--wheel", "mode", flag_value="wheel", help="Wheel file mode.")
@click.option("-r", "--release", "mode", flag_value="release", help="Release ID mode.")
def preprocess(
    ctx: click.Context,
    path: Path,
    distribution: IO[bytes],
    module: list[str] | None = None,
    project: str = "",
    pyversion: str = "",
    depends: list[str] | None = None,
    requirements: Path | None = None,
    mode: (
        Literal["src"] | Literal["dist"] | Literal["wheel"] | Literal["release"]
    ) = "src",
):
    """Preprocess and generate a package distribution file.

    DISTRIBUTION describes the output package distribution file (in json format, use `-` for stdout).

    PATH describes the target path for each mode:

    -s/--src, (default) PATH points to the directory that contains the package code directory

    -d/--dist, PATH points to the directory that contains the package code directory and the .dist-info directory

    -w/--wheel, PATH points to the '.whl' file, which will be unpacked to the same directory as the file

    -r/--release, PATH points to the target directory for downloading and unpacking

    Examples:

    aexpy preprocess -p aexpy@0.1.0 -r ./temp -

    aexpy preprocess -w ./temp/aexpy-0.1.0.whl -

    aexpy preprocess -d ./temp/aexpy-0.1.0 -

    aexpy preprocess ./temp/aexpy-0.1.0 -
    """
    clictx = ctx.ensure_object(CliContext)
    context = preprocessCore(
        service=clictx.service,
        path=path,
        module=module,
        project=project,
        pyversion=pyversion,
        depends=depends,
        requirements=requirements,
        mode=mode,
    )

    result = context.product
    StreamProductSaver(distribution, gzip=clictx.gzip).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.pass_context
@click.argument("distribution", type=click.File("rb"))
@click.argument("description", type=click.File("wb"))
@click.option(
    "-e",
    "--env",
    type=str,
    default="",
    help="Env name, if given, temp option is ignored.",
)
@click.option(
    "--temp/--no-temp",
    default=runInContainer(),
    help="Create a temporary env for extraction, false to use current env.",
)
@click.option(
    "-j",
    "--json",
    "mode",
    flag_value="json",
    default=True,
    help="Preprocessed distribution file mode.",
)
@click.option(
    "-s",
    "--src",
    "mode",
    flag_value="src",
    default=True,
    help="Source code ZIP file mode.",
)
@click.option("-w", "--wheel", "mode", flag_value="wheel", help="Wheel file mode.")
@click.option("-r", "--release", "mode", flag_value="release", help="Release ID mode.")
@click.option(
    "--wheel-name",
    "wheelName",
    default="",
    help="Wheel file name, required when using wheel mode and reading file content from stdin.",
)
def extract(
    ctx: click.Context,
    distribution: IO[bytes],
    description: IO[bytes],
    env: str = "",
    temp: bool = False,
    mode: (
        Literal["json"] | Literal["src"] | Literal["wheel"] | Literal["release"]
    ) = "json",
    wheelName: str = "",
):
    """Extract the API in a distribution.

    DISTRIBUTION describes the input package distribution file (in json format, use `-` for stdin).

    DESCRIPTION describes the output API description file (in json format, use `-` for stdout).

    Mode options describes the processing mode for DISTRIBUTION file.

    -j/--json, (default) DISTRIBUTION file is the JSON file produced by `aexpy preprocess` command

    -s/--src, DISTRIBUTION file is the ZIP file that contains the package code directory

    -w/--wheel, DISTRIBUTION file is the '.whl' file

    -r/--release, DISTRIBUTION file is a text containing the release ID, e.g., aexpy@0.1.0

    Examples:

    aexpy extract ./distribution.json ./api.json

    echo aexpy@0.0.1 | aexpy extract - api.json -r

    aexpy extract ./temp/aexpy-0.1.0.whl api.json -w

    cat ./temp/aexpy-0.1.0.whl | aexpy extract - api.json -w --wheel-name aexpy-0.1.0

    zip -r - ./aexpy | aexpy extract - api.json -s
    """
    clictx = ctx.ensure_object(CliContext)

    if mode == "json":
        data = StreamProductLoader(distribution).load(Distribution)
        context = extractCore(service=clictx.service, data=data, env=env, temp=temp)
    else:
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            if mode == "release":
                context = preprocessCore(
                    service=clictx.service,
                    path=tmpdir,
                    project=distribution.read().decode().strip(),
                    mode="release",
                )
            elif mode == "src":
                unpackedDir = tmpdir / "src"
                with BytesIO(distribution.read()) as bio:
                    with zipfile.ZipFile(bio) as f:
                        f.extractall(unpackedDir)
                context = preprocessCore(
                    service=clictx.service,
                    path=unpackedDir,
                    mode="src",
                )
            elif mode == "wheel":
                # pip install need a valid full wheel name
                if not wheelName:
                    try:
                        wheelName = Path(str(getattr(distribution, "name", ""))).stem
                    except:
                        pass
                wheelName = wheelName.removesuffix(".whl") or "temp"

                wheelFile = tmpdir / f"{wheelName}.whl"
                wheelFile.write_bytes(distribution.read())
                context = preprocessCore(
                    service=clictx.service,
                    path=wheelFile,
                    mode="wheel",
                )
            else:
                raise click.BadOptionUsage("mode", f"Unknown mode value: {mode}")

            if context.product.state != ProduceState.Success:
                context.logger.error(
                    f"Failed to generate Distribution: {context.exception}."
                )
                exitWithContext(context=context)
            data = context.product
            print(data.overview(), file=sys.stderr)

            context = extractCore(service=clictx.service, data=data, env=env, temp=temp)

    result = context.product

    StreamProductSaver(description, gzip=clictx.gzip).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.pass_context
@click.argument("old", type=click.File("rb"))
@click.argument("new", type=click.File("rb"))
@click.argument("difference", type=click.File("wb"))
def diff(ctx: click.Context, old: IO[bytes], new: IO[bytes], difference: IO[bytes]):
    """Diff the API descriptions and find all changes.

    OLD describes the input API description file of the old distribution (in json format, use `-` for stdin).

    NEW describes the input API description file of the new distribution (in json format, use `-` for stdin).

    DIFFERENCE describes the output API difference file (in json format, use `-` for stdout).

    If you have both stdin for OLD and NEW, please split two API descriptions by a comma `,`.

    Examples:

    aexpy diff ./api1.json ./api2.json ./changes.json

    echo "," | cat ./api1.json - ./api2.json | aexpy diff - - ./changes.json
    """
    clictx = ctx.ensure_object(CliContext)

    if old.name == sys.stdin.name and new.name == sys.stdin.name:
        try:
            oldDataDict, newDataDict = json.loads(f"[{old.read().decode()}]")
        except:
            raise click.BadArgumentUsage(
                "Failed to parse two API descriptions from stdin"
            )
        oldData = ApiDescription.model_validate(oldDataDict)
        newData = ApiDescription.model_validate(newDataDict)
    else:
        oldData = StreamProductLoader(old).load(ApiDescription)
        newData = StreamProductLoader(new).load(ApiDescription)

    context = clictx.service.diff(oldData, newData)

    result = context.product
    StreamProductSaver(difference, gzip=clictx.gzip).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.pass_context
@click.argument("difference", type=click.File("rb"))
@click.argument("report", type=click.File("wb"))
def report(ctx: click.Context, difference: IO[bytes], report: IO[bytes]):
    """Generate a report for the API difference file.

    DIFFERENCE describes the input API difference file (in json format, use `-` for stdin).

    REPORT describes the output report file (in json format, use `-` for stdout).

    Examples:

    aexpy report ./changes.json ./report.json
    """
    clictx = ctx.ensure_object(CliContext)

    data = StreamProductLoader(difference).load(ApiDifference)

    context = clictx.service.report(data)

    result = context.product
    StreamProductSaver(report, gzip=clictx.gzip).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    print(f"\n{result.content}", file=sys.stderr)

    if clictx.interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.pass_context
@click.argument("file", type=click.File("rb"))
def view(ctx: click.Context, file: IO[bytes]):
    """View produced data.

    Supports distribution, api-description, api-difference, report and  file (in json format).
    """
    clictx = ctx.ensure_object(CliContext)

    cache = StreamProductLoader(file)

    from .io import load

    result = load(cache.raw(), lambda data: StatSummary.model_validate(data))

    print(result.overview())
    if isinstance(result, Report):
        print(f"\n{result.content}")

    if clictx.interact:
        code.interact(banner="", local=locals())
