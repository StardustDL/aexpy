from aexpy.tools.workers.services import DockerWorkerServiceProvider


def getService():
    return DockerWorkerServiceProvider(tag="stardustdl/aexpy:latest")
