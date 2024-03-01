import code
from io import BytesIO, TextIOWrapper
import json
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import IO, Literal
import zipfile

import click

from aexpy.models import ProduceState

from . import __version__, initializeLogging, runInDocker
from .models import (
    ApiDescription,
    ApiDifference,
    Distribution,
    Product,
    Release,
    Report,
)
from .producers import ProduceContext, produce


FLAG_interact = False
FLAG_gzip = False


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    def resolve_command(self, ctx, args):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        assert cmd is not None, "Command is None."
        return cmd.name, cmd, args


def StreamProductLoader(stream: IO[bytes]):
    from .io.gzip import GzipStreamAutoProductLoader

    return GzipStreamAutoProductLoader(stream)


def StreamProductSaver(target: IO[bytes], logStream: IO[bytes] | None = None):
    if FLAG_gzip:
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


@click.group(cls=AliasedGroup)
@click.pass_context
@click.version_option(
    __version__,
    package_name="aexpy",
    prog_name="aexpy",
    message="%(prog)s v%(version)s",
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
    ctx=None, verbose: int = 0, interact: bool = False, gzip: bool = False
) -> None:
    """
    AexPy /eɪkspaɪ/ is Api EXplorer in PYthon for detecting API breaking changes in Python packages. (ISSRE'22)

    Home page: https://aexpy.netlify.app/

    Repository: https://github.com/StardustDL/aexpy
    """
    global FLAG_interact, FLAG_gzip
    FLAG_interact = interact
    FLAG_gzip = gzip

    loggingLevel = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.NOTSET,
    }[verbose]

    initializeLogging(loggingLevel)


def preprocessCore(
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
        )
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
        from .preprocessing.counter import FileCounterPreprocessor

        with context.using(FileCounterPreprocessor()) as producer:
            producer.preprocess(context.product)
        if not context.product.pyversion:
            context.product.pyversion = "3.12"

    return context


def extractCore(
    data: Distribution,
    env: str = "",
    temp: bool = False,
):
    with produce(ApiDescription(distribution=data)) as context:
        from .extracting.default import DefaultExtractor

        if env:
            from .environments import SingleExecutionEnvironmentBuilder
            from .extracting.environment import getExtractorEnvironment

            envBuilder = SingleExecutionEnvironmentBuilder(
                getExtractorEnvironment(env, context.logger), context.logger
            )
        elif temp:
            from .extracting.environment import getExtractorEnvironmentBuilder

            envBuilder = getExtractorEnvironmentBuilder(context.logger)
        else:
            from .environments import (
                CurrentEnvironment,
                SingleExecutionEnvironmentBuilder,
            )

            envBuilder = SingleExecutionEnvironmentBuilder(
                CurrentEnvironment(context.logger), context.logger
            )

        with envBuilder.use(data.pyversion, context.logger) as eenv:
            with context.using(DefaultExtractor(env=eenv)) as producer:
                producer.extract(data, context.product)

    return context


@main.command()
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
@click.option("-w", "--wheel", "mode", flag_value="wheel", help="Wheel file mode")
@click.option("-r", "--release", "mode", flag_value="release", help="Release ID mode")
def preprocess(
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
    context = preprocessCore(
        path=path,
        module=module,
        project=project,
        pyversion=pyversion,
        depends=depends,
        requirements=requirements,
        mode=mode,
    )

    result = context.product
    StreamProductSaver(distribution).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
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
    default=runInDocker(),
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
@click.option("-w", "--wheel", "mode", flag_value="wheel", help="Wheel file mode")
@click.option("-r", "--release", "mode", flag_value="release", help="Release ID mode")
def extract(
    distribution: IO[bytes],
    description: IO[bytes],
    env: str = "",
    temp: bool = False,
    mode: (
        Literal["json"] | Literal["src"] | Literal["wheel"] | Literal["release"]
    ) = "json",
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

    zip -r - ./aexpy | aexpy extract - api.json -s
    """

    if mode == "json":
        data = StreamProductLoader(distribution).load(Distribution)
        context = extractCore(data, env=env, temp=temp)
    else:
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            if mode == "release":
                context = preprocessCore(
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
                    path=unpackedDir,
                    mode="src",
                )
            elif mode == "wheel":
                wheelFile = tmpdir / "temp.whl"
                wheelFile.write_bytes(distribution.read())
                context = preprocessCore(
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

            context = extractCore(data, env=env, temp=temp)

    result = context.product

    StreamProductSaver(description).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("old", type=click.File("rb"))
@click.argument("new", type=click.File("rb"))
@click.argument("difference", type=click.File("wb"))
def diff(old: IO[bytes], new: IO[bytes], difference: IO[bytes]):
    """Diff the API descriptions and find all changes.

    OLD describes the input API description file of the old distribution (in json format, use `-` for stdin).

    NEW describes the input API description file of the new distribution (in json format, use `-` for stdin).

    DIFFERENCE describes the output API difference file (in json format, use `-` for stdout).

    If you have both stdin for OLD and NEW, please split two API descriptions by a comma `,`.

    Examples:

    aexpy diff ./api1.json ./api2.json ./changes.json

    echo "," | cat ./api1.json - ./api2.json | aexpy diff - - ./changes.json
    """

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

    with produce(
        ApiDifference(old=oldData.distribution, new=newData.distribution)
    ) as context:
        from .diffing.default import DefaultDiffer

        with context.using(DefaultDiffer()) as producer:
            producer.diff(oldData, newData, context.product)

    result = context.product
    StreamProductSaver(difference).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("difference", type=click.File("rb"))
@click.argument("report", type=click.File("wb"))
def report(difference: IO[bytes], report: IO[bytes]):
    """Generate a report for the API difference file.

    DIFFERENCE describes the input API difference file (in json format, use `-` for stdin).

    REPORT describes the output report file (in json format, use `-` for stdout).

    Examples:

    aexpy report ./changes.json ./report.json
    """

    data = StreamProductLoader(difference).load(ApiDifference)

    with produce(Report(old=data.old, new=data.new)) as context:
        from .reporting.text import TextReporter

        with context.using(TextReporter()) as producer:
            producer.report(data, context.product)

    result = context.product
    StreamProductSaver(report).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    print(f"\n{result.content}", file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("file", type=click.File("rb"))
def view(file: IO[bytes]):
    """View produced data.

    Supports distribution, api-description, api-difference, and report file (in json format).
    """

    cache = StreamProductLoader(file)

    from .io import load

    result = load(cache.raw())

    print(result.overview())
    if isinstance(result, Report):
        print(f"\n{result.content}")

    if FLAG_interact:
        code.interact(banner="", local=locals())


if __name__ == "__main__":
    main()
