from aexpy.tools.runners.services import DockerRunnerServiceProvider


def getService():
    return DockerRunnerServiceProvider(tag="stardustdl/aexpy:latest")
