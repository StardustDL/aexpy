import code
import json
import logging
import pathlib
from pathlib import Path
import sys
from typing import IO, Annotated, Literal

import click
from pydantic import Field

from aexpy.models import ProduceState
from aexpy.caching import (
    FileProduceCache,
    StreamReaderProduceCache,
    StreamWriterProduceCache,
)

from . import __version__, initializeLogging, runInDocker
from .models import (
    ApiDescription,
    ApiDifference,
    Distribution,
    Product,
    Release,
    ReleasePair,
    Report,
)
from .producers import ProduceContext, produce


FLAG_interact = False


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
def main(ctx=None, verbose: int = 0, interact: bool = False) -> None:
    """
    AexPy /eɪkspaɪ/ is Api EXplorer in PYthon for detecting API breaking changes in Python packages. (ISSRE'22)

    Home page: https://aexpy.netlify.app/

    Repository: https://github.com/StardustDL/aexpy
    """
    global FLAG_interact
    FLAG_interact = interact

    loggingLevel = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.NOTSET,
    }[verbose]

    initializeLogging(loggingLevel)


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
@click.argument("distribution", type=click.File("w"))
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
    distribution: IO[str],
    module: list[str] | None = None,
    project: str = "",
    pyversion: str = "",
    depends: list[str] | None = None,
    requirements: Path | None = None,
    mode: Literal["src"]
    | Literal["dist"]
    | Literal["wheel"]
    | Literal["release"] = "src",
):
    """Preprocess and generate a package distribution file.

    DISTRIBUTION describes the output package distribution file (in json format, use `-` for stdout).

    PATH describes the target path for each mode:

    mode=src, PATH points to the directory that contains the package code directory

    mode=dist, PATH points to the directory that contains the package code directory and the .dist-info directory

    mode=wheel, PATH points to the '.whl' file, which will be unpacked to the same directory as the file

    mode=release, PATH points to the target directory for downloading and unpacking

    Examples:

    aexpy preprocess -p aexpy@0.1.0 -r ./temp -

    aexpy preprocess -w ./temp/aexpy-0.1.0.whl -

    aexpy preprocess -d ./temp/aexpy-0.1.0 -

    aexpy preprocess ./temp/aexpy-0.1.0 -
    """
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

            preprocessor = PipWheelDownloadPreprocessor(
                cacheDir=path, logger=context.logger
            )
            context.use(preprocessor)
            preprocessor.preprocess(context.product)
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
            preprocessor = WheelUnpackPreprocessor(cacheDir=path, logger=context.logger)
            context.use(preprocessor)
            preprocessor.preprocess(context.product)
            mode = "dist"

        if mode == "dist":
            assert path.is_dir(), "The target path should be a directory."
            from .preprocessing.wheel import WheelMetadataPreprocessor

            preprocessor = WheelMetadataPreprocessor(logger=context.logger)
            context.use(preprocessor)
            preprocessor.preprocess(context.product)
            mode = "src"

        assert mode == "src"
        assert path.is_dir(), "The target path should be a directory."
        from .preprocessing.counter import FileCounterPreprocessor

        preprocessor = FileCounterPreprocessor(context.logger)
        context.use(preprocessor)
        preprocessor.preprocess(context.product)

    result = context.product
    StreamWriterProduceCache(distribution).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("distribution", type=click.File("r"))
@click.argument("description", type=click.File("w"))
@click.option(
    "-e",
    "--env",
    type=str,
    default="",
    help="Conda env name, if given, temp option is ignored.",
)
@click.option(
    "--temp/--no-temp",
    default=runInDocker(),
    help="Create a temporary conda env for extraction, false to use current env.",
)
def extract(
    distribution: IO[str], description: IO[str], env: str = "", temp: bool = False
):
    """Extract the API in a distribution.

    DISTRIBUTION describes the input package distribution file (in json format, use `-` for stdin).

    DESCRIPTION describes the output API description file (in json format, use `-` for stdout).

    Examples:

    aexpy extract ./distribution1.json ./api1.json
    """

    data = StreamReaderProduceCache(distribution).data(Distribution)
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
            extractor = DefaultExtractor(env=eenv, logger=context.logger)
            context.use(extractor)
            extractor.extract(data, context.product)

    result = context.product
    StreamWriterProduceCache(description).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("old", type=click.File("r"))
@click.argument("new", type=click.File("r"))
@click.argument("difference", type=click.File("w"))
def diff(old: IO[str], new: IO[str], difference: IO[str]):
    """Diff the API description and find all changes.

    OLD describes the input API description file of the old distribution (in json format, use `-` for stdin).

    NEW describes the input API description file of the new distribution (in json format, use `-` for stdin).

    DIFFERENCE describes the output API difference file (in json format, use `-` for stdout).

    Examples:

    aexpy diff ./api1.json ./api2.json ./changes.json
    """
    oldData = StreamReaderProduceCache(old).data(ApiDescription)
    newData = StreamReaderProduceCache(new).data(ApiDescription)

    with produce(
        ApiDifference(old=oldData.distribution, new=newData.distribution)
    ) as context:
        from .diffing.default import DefaultDiffer

        differ = DefaultDiffer(logger=context.logger)
        context.use(differ)
        differ.diff(oldData, newData, context.product)

    result = context.product
    StreamWriterProduceCache(difference).save(result, context.log)

    print(result.overview(), file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("difference", type=click.File("r"))
@click.argument("report", type=click.File("w"))
def report(difference: IO[str], report: IO[str]):
    """Generate a report for the API difference file.

    DIFFERENCE describes the input API difference file (in json format, use `-` for stdin).

    REPORT describes the output report file (in json format, use `-` for stdout).

    Examples:

    aexpy report ./changes.json ./report.json
    """

    data = StreamReaderProduceCache(difference).data(ApiDifference)

    with produce(Report(old=data.old, new=data.new)) as context:
        from .reporting.text import TextReporter

        reporter = TextReporter(logger=context.logger)
        context.use(reporter)
        reporter.report(data, context.product)

    result = context.product
    StreamWriterProduceCache(report).save(result, context.log)

    print(result.overview(), file=sys.stderr)
    print(f"\n{result.content}", file=sys.stderr)

    if FLAG_interact:
        code.interact(banner="", local=locals())

    exitWithContext(context=context)


@main.command()
@click.argument("file", type=click.File("r"))
def view(file: IO[str]):
    """View produced data.

    Supports distribution, api-description, api-difference, and report file (in json format).
    """

    cache = StreamReaderProduceCache(file)

    try:
        data = json.loads(cache.raw())
        if "release" in data:
            result = Distribution.model_validate(data)
        elif "distribution" in data:
            result = ApiDescription.model_validate(data)
        elif "entries" in data:
            result = ApiDifference.model_validate(data)
        else:
            result = Report.model_validate(data)
    except Exception as ex:
        assert False, f"Failed to load data: {ex}"

    print(result.overview())
    if isinstance(result, Report):
        print(f"\n{result.content}")

    if FLAG_interact:
        code.interact(banner="", local=locals())


if __name__ == "__main__":
    main()
