import os
import pathlib
import shutil
from string import Template
from aexpy.env import env
from aexpy import fsutils
import subprocess
import sys

DOCKERFILE_TEMPLATE = Template("""FROM python:$pythonVersion

COPY ./analyses /app/analyses

COPY ./$targetPackage /deps/$targetPackage

RUN [ "pip", "install", "/deps/$targetPackage" ]

WORKDIR /app

ENTRYPOINT [ "python", "-u", "-m", "analyses", "$targetPackage", "$topLevelModule" ]""")


class DynamicAnalysisEnvironment:
    def __init__(self, packageFile: pathlib.Path, topLevelModule: str = "", pythonVersion: str = 3.6) -> None:
        self.packageFile = packageFile
        self.pythonVersion = pythonVersion
        self.topLevelModule = topLevelModule

        cache = env.cache.joinpath("analysis")
        fsutils.ensureDirectory(cache)
        self.buildDirectory = cache.joinpath("build")
        fsutils.ensureDirectory(self.buildDirectory)

        self.dockerfile = cache.joinpath(self.packageFile.stem)
        self.image = f"aexpy-docker-{self.packageFile.stem}".lower()

    def generateDockerfile(self) -> pathlib.Path:
        if not self.dockerfile.exists() or env.dev:
            content = DOCKERFILE_TEMPLATE.substitute(
                pythonVersion=self.pythonVersion,
                aexpy=pathlib.Path(__file__).parent.parent.parent.absolute().as_posix(),
                targetPackage=self.packageFile.name,
                topLevelModule=self.topLevelModule)
            self.dockerfile.write_text(content)
        return self.dockerfile.absolute()

    def buildImage(self) -> str:
        src = self.buildDirectory.joinpath("analyses")
        if not src.exists() or env.dev:
            if src.exists():
                shutil.rmtree(src)
            shutil.copytree(pathlib.Path(__file__).parent, src)

        toPackage = self.buildDirectory.joinpath(self.packageFile.name)
        shutil.copyfile(self.packageFile, toPackage)
        subprocess.check_call(["docker", "build", "-t", self.image,
                              "-f", str(self.dockerfile.absolute().as_posix()), str(self.buildDirectory.absolute().as_posix())])
        os.remove(toPackage)
        return self.image

    def run(self):
        return subprocess.check_output(["docker", "run", "--rm", self.image]).decode()

    def cleanImage(self):
        subprocess.check_output(["docker", "rmi", self.image])
    
    def __enter__(self) -> str:
        self.generateDockerfile()
        self.buildImage()
        return self.run()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanImage()
